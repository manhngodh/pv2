"""Base exchange interface for Passivbot."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Dict, Any
import asyncio
import logging

from ..core.config import ExchangeConfig
from ..core.types import (
    Order, Position, Balance, Trade, MarketData,
    OrderSide, OrderType, OrderStatus, Symbol
)
from ..core.exceptions import (
    ExchangeError, ExchangeConnectionError, ExchangeAPIError,
    InsufficientBalanceError, OrderError
)

logger = logging.getLogger(__name__)


class BaseExchange(ABC):
    """Abstract base class for exchange implementations."""
    
    def __init__(self, config: ExchangeConfig) -> None:
        """Initialize exchange.
        
        Args:
            config: Exchange configuration
        """
        self.config = config
        self._connected = False
        self._rate_limiter = asyncio.Semaphore(config.rate_limit)
        self._session = None
    
    @property
    def is_connected(self) -> bool:
        """Check if exchange is connected."""
        return self._connected
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the exchange."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange."""
        pass
    
    async def close(self) -> None:
        """Close exchange connection."""
        await self.disconnect()
    
    # Account and Balance Methods
    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """Get account balances.
        
        Returns:
            List of account balances
        """
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str) -> Optional[Balance]:
        """Get balance for specific asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            Balance for the asset or None if not found
        """
        pass
    
    # Position Methods
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get open positions.
        
        Returns:
            List of open positions
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position for the symbol or None if not found
        """
        pass
    
    # Order Methods
    @abstractmethod
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
        """Place a trading order.
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            order_type: Order type
            quantity: Order quantity
            price: Order price (required for limit orders)
            client_id: Client order ID
            **kwargs: Additional order parameters
            
        Returns:
            Placed order
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Order details or None if not found
        """
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        pass
    
    # Market Data Methods
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Market data
        """
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for symbol.
        
        Args:
            symbol: Trading symbol
            limit: Number of levels to return
            
        Returns:
            Orderbook data
        """
        pass
    
    # Trading Methods
    async def buy_market(self, symbol: str, quantity: Decimal, **kwargs) -> Order:
        """Place market buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            **kwargs: Additional parameters
            
        Returns:
            Placed order
        """
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity,
            **kwargs
        )
    
    async def sell_market(self, symbol: str, quantity: Decimal, **kwargs) -> Order:
        """Place market sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            **kwargs: Additional parameters
            
        Returns:
            Placed order
        """
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            **kwargs
        )
    
    async def buy_limit(self, symbol: str, quantity: Decimal, price: Decimal, **kwargs) -> Order:
        """Place limit buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            **kwargs: Additional parameters
            
        Returns:
            Placed order
        """
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            **kwargs
        )
    
    async def sell_limit(self, symbol: str, quantity: Decimal, price: Decimal, **kwargs) -> Order:
        """Place limit sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            **kwargs: Additional parameters
            
        Returns:
            Placed order
        """
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            **kwargs
        )
    
    # Utility Methods
    async def _rate_limited_request(self, coro):
        """Execute request with rate limiting.
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Coroutine result
        """
        async with self._rate_limiter:
            return await coro
    
    def _validate_symbol(self, symbol: str) -> None:
        """Validate trading symbol format.
        
        Args:
            symbol: Trading symbol
            
        Raises:
            ValueError: If symbol format is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
    
    def _validate_quantity(self, quantity: Decimal) -> None:
        """Validate order quantity.
        
        Args:
            quantity: Order quantity
            
        Raises:
            ValueError: If quantity is invalid
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    def _validate_price(self, price: Optional[Decimal]) -> None:
        """Validate order price.
        
        Args:
            price: Order price
            
        Raises:
            ValueError: If price is invalid
        """
        if price is not None and price <= 0:
            raise ValueError("Price must be positive")
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.config.type})"
    
    def __repr__(self) -> str:
        """Representation."""
        return f"{self.__class__.__name__}(type={self.config.type}, testnet={self.config.testnet})"
