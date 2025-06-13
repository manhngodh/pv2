"""Bybit exchange implementation."""

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


class BybitExchange(BaseExchange):
    """Bybit exchange implementation."""
    
    def __init__(self, config: ExchangeConfig) -> None:
        """Initialize Bybit exchange.
        
        Args:
            config: Exchange configuration
        """
        super().__init__(config)
        
        # Set API endpoints
        if config.testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
    
    async def connect(self) -> None:
        """Connect to Bybit API."""
        try:
            # Create HTTP session
            self._session = aiohttp.ClientSession()
            
            # Test connection
            await self._test_connection()
            
            self._connected = True
            logger.info(f"Connected to Bybit ({self.config.type})")
            
        except Exception as e:
            logger.error(f"Failed to connect to Bybit: {e}")
            if self._session:
                await self._session.close()
                self._session = None
            raise ExchangeConnectionError(f"Failed to connect to Bybit: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Bybit API."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        logger.info("Disconnected from Bybit")
    
    async def _test_connection(self) -> None:
        """Test API connection."""
        endpoint = "/v5/market/time"
        response = await self._make_request("GET", endpoint)
        
        if "time" not in response.get("result", {}):
            raise ExchangeAPIError("Invalid response from server time endpoint")
        
        logger.debug("Bybit connection test successful")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """Make HTTP request to Bybit API.
        
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
            headers["X-BAPI-API-KEY"] = self.config.api_key
            # TODO: Add signature generation for Bybit
        
        async with self._rate_limiter:
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers
                ) as response:
                    data = await response.json()
                    
                    # Bybit uses retCode for status
                    if data.get("retCode") != 0:
                        error_msg = data.get("retMsg", f"HTTP {response.status}")
                        raise ExchangeAPIError(
                            error_msg,
                            status_code=response.status,
                            error_code=str(data.get("retCode"))
                        )
                    
                    return data
                    
            except aiohttp.ClientError as e:
                raise ExchangeConnectionError(f"Connection error: {e}")
    
    # Simplified implementations - would need full Bybit API integration
    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        # Placeholder implementation
        logger.warning("Bybit get_balances not fully implemented")
        return []
    
    async def get_balance(self, asset: str) -> Optional[Balance]:
        """Get balance for specific asset."""
        balances = await self.get_balances()
        return next((b for b in balances if b.asset == asset), None)
    
    async def get_positions(self) -> List[Position]:
        """Get open positions."""
        logger.warning("Bybit get_positions not fully implemented")
        return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol."""
        positions = await self.get_positions()
        return next((p for p in positions if p.symbol == symbol), None)
    
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
        logger.warning("Bybit place_order not fully implemented")
        # Return a dummy order for now
        from uuid import uuid4
        return Order(
            id=str(uuid4()),
            client_id=client_id or str(uuid4()),
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        logger.warning("Bybit cancel_order not fully implemented")
        return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details."""
        logger.warning("Bybit get_order not fully implemented")
        return None
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders."""
        logger.warning("Bybit get_open_orders not fully implemented")
        return []
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data for symbol."""
        endpoint = "/v5/market/tickers"
        params = {"category": "spot", "symbol": symbol}
        
        response = await self._make_request("GET", endpoint, params)
        
        if not response.get("result", {}).get("list"):
            raise ExchangeAPIError(f"No market data found for {symbol}")
        
        ticker = response["result"]["list"][0]
        
        return MarketData(
            symbol=ticker["symbol"],
            price=Decimal(ticker["lastPrice"]),
            bid=Decimal(ticker["bid1Price"]) if ticker.get("bid1Price") else None,
            ask=Decimal(ticker["ask1Price"]) if ticker.get("ask1Price") else None,
            volume_24h=Decimal(ticker["volume24h"]) if ticker.get("volume24h") else None,
            change_24h=Decimal(ticker["price24hPcnt"]) if ticker.get("price24hPcnt") else None
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for symbol."""
        endpoint = "/v5/market/orderbook"
        params = {
            "category": "spot",
            "symbol": symbol,
            "limit": min(limit, 500)  # Bybit limit
        }
        
        return await self._make_request("GET", endpoint, params)
