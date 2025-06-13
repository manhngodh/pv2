"""Binance exchange implementation."""

from decimal import Decimal
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

import aiohttp

from .base import BaseExchange
from ..core.config import ExchangeConfig
from ..core.types import (
    Order, Position, Balance, Trade, MarketData,
    OrderSide, OrderType, OrderStatus
)
from ..core.exceptions import (
    ExchangeError, ExchangeConnectionError, ExchangeAPIError,
    InsufficientBalanceError
)

logger = logging.getLogger(__name__)


class BinanceExchange(BaseExchange):
    """Binance exchange implementation."""
    
    def __init__(self, config: ExchangeConfig) -> None:
        """Initialize Binance exchange.
        
        Args:
            config: Exchange configuration
        """
        super().__init__(config)
        
        # Set API endpoints
        if config.testnet:
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        # For futures
        if config.type == "binance_futures":
            if config.testnet:
                self.base_url = "https://testnet.binancefuture.com"
            else:
                self.base_url = "https://fapi.binance.com"
    
    async def connect(self) -> None:
        """Connect to Binance API."""
        try:
            # Create HTTP session
            self._session = aiohttp.ClientSession()
            
            # Test connection
            await self._test_connection()
            
            self._connected = True
            logger.info(f"Connected to Binance ({self.config.type})")
            
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            if self._session:
                await self._session.close()
                self._session = None
            raise ExchangeConnectionError(f"Failed to connect to Binance: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Binance API."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        logger.info("Disconnected from Binance")
    
    async def _test_connection(self) -> None:
        """Test API connection."""
        endpoint = "/api/v3/time"
        response = await self._make_request("GET", endpoint)
        
        if "serverTime" not in response:
            raise ExchangeAPIError("Invalid response from server time endpoint")
        
        logger.debug("Binance connection test successful")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """Make HTTP request to Binance API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs authentication
            
        Returns:
            API response data
        """
        if not self._session:
            raise ExchangeConnectionError("Not connected to exchange")
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add API key if signed request
        if signed:
            headers["X-MBX-APIKEY"] = self.config.api_key
            # TODO: Add signature generation
        
        async with self._rate_limiter:
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers
                ) as response:
                    data = await response.json()
                    
                    if response.status != 200:
                        error_msg = data.get("msg", f"HTTP {response.status}")
                        raise ExchangeAPIError(
                            error_msg,
                            status_code=response.status,
                            error_code=data.get("code")
                        )
                    
                    return data
                    
            except aiohttp.ClientError as e:
                raise ExchangeConnectionError(f"Connection error: {e}")
    
    # Account and Balance Methods
    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        endpoint = "/api/v3/account"
        response = await self._make_request("GET", endpoint, signed=True)
        
        balances = []
        for balance_data in response.get("balances", []):
            if float(balance_data["free"]) > 0 or float(balance_data["locked"]) > 0:
                balance = Balance(
                    asset=balance_data["asset"],
                    free=Decimal(balance_data["free"]),
                    locked=Decimal(balance_data["locked"])
                )
                balances.append(balance)
        
        return balances
    
    async def get_balance(self, asset: str) -> Optional[Balance]:
        """Get balance for specific asset."""
        balances = await self.get_balances()
        return next((b for b in balances if b.asset == asset), None)
    
    # Position Methods (for spot trading, positions are derived from balances)
    async def get_positions(self) -> List[Position]:
        """Get open positions (for spot, this returns non-zero balances)."""
        # For spot trading, positions are represented by non-zero balances
        # For futures, this would query the futures positions endpoint
        return []  # Simplified for now
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol."""
        positions = await self.get_positions()
        return next((p for p in positions if p.symbol == symbol), None)
    
    # Order Methods
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        client_id: Optional[str] = None,
        **kwargs
    ) -> Order:
        """Place a trading order."""
        self._validate_symbol(symbol)
        self._validate_quantity(quantity)
        
        if order_type == OrderType.LIMIT:
            self._validate_price(price)
        
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "side": side.value.upper(),
            "type": order_type.value.upper(),
            "quantity": str(quantity),
        }
        
        if price is not None:
            params["price"] = str(price)
        
        if client_id:
            params["newClientOrderId"] = client_id
        
        # Add default time in force for limit orders
        if order_type == OrderType.LIMIT:
            params["timeInForce"] = "GTC"  # Good Till Cancel
        
        try:
            response = await self._make_request("POST", endpoint, params, signed=True)
            return self._parse_order_response(response)
            
        except ExchangeAPIError as e:
            if "insufficient" in str(e).lower():
                raise InsufficientBalanceError(
                    required_balance=quantity,
                    available_balance=Decimal("0"),  # Would need to fetch actual balance
                    asset=symbol.split("USDT")[0] if "USDT" in symbol else symbol
                )
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        
        try:
            await self._make_request("DELETE", endpoint, params, signed=True)
            return True
        except ExchangeAPIError:
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details."""
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        
        try:
            response = await self._make_request("GET", endpoint, params, signed=True)
            return self._parse_order_response(response)
        except ExchangeAPIError:
            return None
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders."""
        endpoint = "/api/v3/openOrders"
        params = {}
        
        if symbol:
            params["symbol"] = symbol
        
        response = await self._make_request("GET", endpoint, params, signed=True)
        return [self._parse_order_response(order_data) for order_data in response]
    
    # Market Data Methods
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data for symbol."""
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        response = await self._make_request("GET", endpoint, params)
        
        return MarketData(
            symbol=response["symbol"],
            price=Decimal(response["lastPrice"]),
            bid=Decimal(response["bidPrice"]),
            ask=Decimal(response["askPrice"]),
            volume_24h=Decimal(response["volume"]),
            change_24h=Decimal(response["priceChangePercent"])
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for symbol."""
        endpoint = "/api/v3/depth"
        params = {
            "symbol": symbol,
            "limit": min(limit, 5000)  # Binance limit
        }
        
        return await self._make_request("GET", endpoint, params)
    
    def _parse_order_response(self, response: Dict[str, Any]) -> Order:
        """Parse order response from Binance API."""
        # Map Binance status to our status
        status_map = {
            "NEW": OrderStatus.OPEN,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.CANCELLED,
        }
        
        return Order(
            id=str(response["orderId"]),
            client_id=response.get("clientOrderId", ""),
            symbol=response["symbol"],
            side=OrderSide(response["side"].lower()),
            type=OrderType(response["type"].lower()),
            quantity=Decimal(response["origQty"]),
            price=Decimal(response["price"]) if response["price"] != "0.00000000" else None,
            status=status_map.get(response["status"], OrderStatus.PENDING),
            filled_quantity=Decimal(response["executedQty"]),
            timestamp=datetime.fromtimestamp(response["time"] / 1000) if "time" in response else datetime.utcnow(),
            updated_at=datetime.fromtimestamp(response["updateTime"] / 1000) if "updateTime" in response else datetime.utcnow()
        )
