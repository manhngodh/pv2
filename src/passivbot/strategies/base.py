"""Base strategy interface for Passivbot."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from ..core.config import StrategyConfig
from ..core.types import Order, Position, Balance, MarketData, OrderSide, OrderType
from ..core.exceptions import StrategyError, StrategyExecutionError, RiskManagementError
from ..exchanges.base import BaseExchange

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""
    
    def __init__(
        self, 
        config: StrategyConfig, 
        exchange: BaseExchange, 
        dry_run: bool = False
    ) -> None:
        """Initialize strategy.
        
        Args:
            config: Strategy configuration
            exchange: Exchange instance
            dry_run: Whether to run in dry mode
        """
        self.config = config
        self.exchange = exchange
        self.dry_run = dry_run
        self.is_active = config.enabled
        
        # Strategy state
        self._orders: Dict[str, Order] = {}
        self._position: Optional[Position] = None
        self._market_data: Optional[MarketData] = None
        self._last_execution = datetime.utcnow()
        
        logger.info(f"Initialized {config.type} strategy for {config.symbol}")
    
    @property
    def symbol(self) -> str:
        """Get trading symbol."""
        return self.config.symbol
    
    @property
    def strategy_type(self) -> str:
        """Get strategy type."""
        return self.config.type.value
    
    @abstractmethod
    async def execute(self) -> None:
        """Execute strategy logic."""
        pass
    
    @abstractmethod
    async def calculate_orders(self) -> List[Order]:
        """Calculate orders to place based on strategy logic.
        
        Returns:
            List of orders to place
        """
        pass
    
    async def update_market_data(self) -> None:
        """Update market data for the symbol."""
        try:
            self._market_data = await self.exchange.get_market_data(self.symbol)
        except Exception as e:
            logger.warning(f"Failed to update market data for {self.symbol}: {e}")
    
    async def update_position(self) -> None:
        """Update current position."""
        try:
            self._position = await self.exchange.get_position(self.symbol)
        except Exception as e:
            logger.warning(f"Failed to update position for {self.symbol}: {e}")
    
    async def update_orders(self) -> None:
        """Update open orders."""
        try:
            open_orders = await self.exchange.get_open_orders(self.symbol)
            self._orders = {order.id: order for order in open_orders if order.id}
        except Exception as e:
            logger.warning(f"Failed to update orders for {self.symbol}: {e}")
    
    async def place_order(
        self,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        **kwargs
    ) -> Optional[Order]:
        """Place an order.
        
        Args:
            side: Order side
            order_type: Order type
            quantity: Order quantity
            price: Order price
            **kwargs: Additional parameters
            
        Returns:
            Placed order or None if dry run
        """
        if self.dry_run:
            logger.info(
                f"DRY RUN: Would place {side.value} {order_type.value} order "
                f"for {quantity} {self.symbol} at {price}"
            )
            return None
        
        try:
            order = await self.exchange.place_order(
                symbol=self.symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                **kwargs
            )
            
            # Store order
            if order.id:
                self._orders[order.id] = order
            
            logger.info(f"Placed {side.value} order {order.id} for {quantity} {self.symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise StrategyExecutionError(f"Failed to place order: {e}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        if self.dry_run:
            logger.info(f"DRY RUN: Would cancel order {order_id}")
            return True
        
        try:
            success = await self.exchange.cancel_order(order_id, self.symbol)
            
            if success and order_id in self._orders:
                del self._orders[order_id]
                logger.info(f"Cancelled order {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def cancel_all_orders(self) -> int:
        """Cancel all open orders.
        
        Returns:
            Number of orders cancelled
        """
        cancelled = 0
        for order_id in list(self._orders.keys()):
            if await self.cancel_order(order_id):
                cancelled += 1
        
        return cancelled
    
    async def get_current_price(self) -> Optional[Decimal]:
        """Get current market price.
        
        Returns:
            Current price or None if not available
        """
        if self._market_data:
            return self._market_data.price
        
        await self.update_market_data()
        return self._market_data.price if self._market_data else None
    
    async def get_balance(self, asset: str) -> Optional[Balance]:
        """Get balance for specific asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            Balance or None if not found
        """
        try:
            return await self.exchange.get_balance(asset)
        except Exception as e:
            logger.warning(f"Failed to get balance for {asset}: {e}")
            return None
    
    def calculate_quantity_from_percentage(
        self, 
        balance: Balance, 
        percentage: Decimal
    ) -> Decimal:
        """Calculate quantity from balance percentage.
        
        Args:
            balance: Account balance
            percentage: Percentage of balance to use
            
        Returns:
            Calculated quantity
        """
        return balance.free * (percentage / Decimal("100"))
    
    def calculate_grid_levels(
        self,
        current_price: Decimal,
        num_levels: int,
        spacing_percentage: Decimal,
        upper_price: Optional[Decimal] = None,
        lower_price: Optional[Decimal] = None
    ) -> List[Decimal]:
        """Calculate grid price levels.
        
        Args:
            current_price: Current market price
            num_levels: Number of grid levels
            spacing_percentage: Price spacing between levels
            upper_price: Upper boundary (optional)
            lower_price: Lower boundary (optional)
            
        Returns:
            List of price levels
        """
        levels = []
        spacing = spacing_percentage / Decimal("100")
        
        # Calculate levels above current price
        for i in range(1, num_levels // 2 + 1):
            price = current_price * (Decimal("1") + spacing * i)
            if upper_price is None or price <= upper_price:
                levels.append(price)
        
        # Add current price level
        levels.append(current_price)
        
        # Calculate levels below current price
        for i in range(1, num_levels // 2 + 1):
            price = current_price * (Decimal("1") - spacing * i)
            if lower_price is None or price >= lower_price:
                levels.insert(0, price)
        
        return sorted(levels)
    
    async def cleanup(self) -> None:
        """Cleanup strategy resources."""
        if not self.dry_run:
            cancelled = await self.cancel_all_orders()
            if cancelled > 0:
                logger.info(f"Cancelled {cancelled} orders during cleanup")
    
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status.
        
        Returns:
            Strategy status information
        """
        return {
            "symbol": self.symbol,
            "type": self.strategy_type,
            "active": self.is_active,
            "dry_run": self.dry_run,
            "open_orders": len(self._orders),
            "current_price": str(self._market_data.price) if self._market_data else None,
            "last_execution": self._last_execution.isoformat(),
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.symbol})"
    
    def __repr__(self) -> str:
        """Representation."""
        return f"{self.__class__.__name__}(symbol={self.symbol}, type={self.strategy_type})"
