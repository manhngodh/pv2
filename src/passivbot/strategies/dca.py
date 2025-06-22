"""DCA (Dollar Cost Averaging) strategy implementation."""

from decimal import Decimal
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from .base import BaseStrategy
from ..core.config import StrategyConfig
from ..core.types import Order, OrderSide, OrderType, OrderStatus
from ..core.exceptions import StrategyError, StrategyExecutionError
from ..exchanges.base import BaseExchange

logger = logging.getLogger(__name__)


class DCAStrategy(BaseStrategy):
    """DCA (Dollar Cost Averaging) strategy implementation."""
    
    def __init__(
        self, 
        config: StrategyConfig, 
        exchange: BaseExchange, 
        dry_run: bool = False
    ) -> None:
        """Initialize DCA strategy.
        
        Args:
            config: Strategy configuration
            exchange: Exchange instance
            dry_run: Whether to run in dry mode
        """
        super().__init__(config, exchange, dry_run)
        
        if not config.dca_config:
            raise StrategyError("DCA configuration is required for DCA strategy")
        
        self.dca_config = config.dca_config
        self._base_order: Optional[Order] = None
        self._safety_orders: List[Order] = []
        self._take_profit_order: Optional[Order] = None
        self._entry_price: Optional[Decimal] = None
        self._safety_order_count = 0
        self._initialized = False
        self._position_size = Decimal("0")  # Track total position size
        
        logger.info(
            f"DCA strategy initialized: Base order {self.dca_config.base_order_size}, "
            f"Safety orders {self.dca_config.safety_order_size}, "
            f"Max safety orders {self.dca_config.max_safety_orders}"
        )
    
    async def execute(self) -> None:
        """Execute DCA strategy logic."""
        if not self.is_active:
            return
        
        try:
            # Update market data
            await self.update_market_data()
            await self.update_orders()
            await self.update_position()
            
            if not self._market_data:
                logger.warning(f"No market data available for {self.symbol}")
                return
            
            # Initialize DCA if not done and no active position
            if not self._initialized and self._position_size <= 0:
                await self._initialize_dca()
                self._initialized = True
            
            # Check for filled orders and manage DCA
            await self._manage_dca_orders()
            
            # Check stop loss if configured
            if self.dca_config.stop_loss_percentage:
                await self._check_stop_loss()
            
            self._last_execution = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error executing DCA strategy for {self.symbol}: {e}")
            raise StrategyExecutionError(f"DCA strategy execution failed: {e}")
    
    async def calculate_orders(self) -> List[Order]:
        """Calculate orders to place based on DCA logic.
        
        Returns:
            List of orders to place
        """
        orders = []
        
        if not self._market_data:
            return orders
        
        current_price = self._market_data.price
        
        # Base order (first buy)
        if not self._base_order:
            orders.append(Order(
                symbol=self.symbol,
                side=OrderSide.BUY,
                type=OrderType.MARKET,  # Market order for immediate execution
                quantity=self.dca_config.base_order_size / current_price,
                status=OrderStatus.PENDING
            ))
        
        # Safety orders
        if self._entry_price and self._safety_order_count < self.dca_config.max_safety_orders:
            deviation = self.dca_config.price_deviation_percentage / Decimal("100")
            
            for i in range(self._safety_order_count, self.dca_config.max_safety_orders):
                # Calculate safety order price with step scaling
                step_multiplier = self.dca_config.safety_order_step_scale ** i
                safety_price = self._entry_price * (Decimal("1") - deviation * step_multiplier)
                
                if current_price <= safety_price:
                    # Calculate quantity with volume scaling
                    volume_multiplier = self.dca_config.safety_order_volume_scale ** i
                    safety_quantity = (self.dca_config.safety_order_size * volume_multiplier) / safety_price
                    
                    orders.append(Order(
                        symbol=self.symbol,
                        side=OrderSide.BUY,
                        type=OrderType.LIMIT,
                        quantity=safety_quantity,
                        price=safety_price,
                        status=OrderStatus.PENDING
                    ))
        
        return orders
    
    async def _initialize_dca(self) -> None:
        """Initialize DCA strategy by placing base order."""
        if not self._market_data:
            return
        
        current_price = self._market_data.price
        
        # Check if we have enough balance for base order
        quote_balance = await self.get_balance("USDT")  # Assuming USDT pairs
        if not quote_balance or quote_balance.free < self.dca_config.base_order_size:
            logger.warning(f"Insufficient balance for base order: {quote_balance}")
            return
        
        # Place base order
        base_quantity = self.dca_config.base_order_size / current_price
        
        try:
            self._base_order = await self.place_order(
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=base_quantity
            )
            
            if self._base_order:
                self._entry_price = current_price  # Use current price for market orders
                self._position_size = base_quantity
                logger.info(f"DCA base order placed: {base_quantity} at market price {current_price}")
                logger.info(f"DCA position initialized: {self._position_size} BTC at ${self._entry_price}")
                
                # Place take profit order immediately
                await self._place_take_profit_order()
                
                # Place first safety order
                await self._place_safety_orders()
        
        except Exception as e:
            logger.error(f"Failed to place DCA base order: {e}")
    
    async def _manage_dca_orders(self) -> None:
        """Manage DCA orders and check for fills."""
        # Check base order status
        if self._base_order and self._base_order.id:
            updated_order = await self.exchange.get_order(self._base_order.id, self.symbol)
            if updated_order and updated_order.is_filled and self._base_order.status != OrderStatus.FILLED:
                self._base_order.status = OrderStatus.FILLED  # Mark as handled
                await self._handle_base_order_fill(updated_order)
        
        # Check safety orders
        for i, safety_order in enumerate(self._safety_orders):
            if safety_order.id:
                updated_order = await self.exchange.get_order(safety_order.id, self.symbol)
                if updated_order and updated_order.is_filled and safety_order.status != OrderStatus.FILLED:
                    safety_order.status = OrderStatus.FILLED  # Mark as handled
                    await self._handle_safety_order_fill(updated_order, i)
        
        # Check take profit order
        if self._take_profit_order and self._take_profit_order.id:
            updated_order = await self.exchange.get_order(self._take_profit_order.id, self.symbol)
            if updated_order and updated_order.is_filled and self._take_profit_order.status != OrderStatus.FILLED:
                self._take_profit_order.status = OrderStatus.FILLED  # Mark as handled
                await self._handle_take_profit_fill(updated_order)
        
        # Place new safety orders if needed
        await self._place_safety_orders()
    
    async def _handle_base_order_fill(self, filled_order: Order) -> None:
        """Handle base order fill.
        
        Args:
            filled_order: The filled base order
        """
        if filled_order.average_price:
            self._entry_price = filled_order.average_price
            self._position_size = filled_order.quantity
            logger.info(f"DCA base order filled at {self._entry_price}, position: {self._position_size}")
            
            # Place take profit order
            await self._place_take_profit_order()
            
            # Place first safety order
            await self._place_safety_orders()
    
    async def _handle_safety_order_fill(self, filled_order: Order, order_index: int) -> None:
        """Handle safety order fill.
        
        Args:
            filled_order: The filled safety order
            order_index: Index of the safety order
        """
        logger.info(f"DCA safety order {order_index + 1} filled at {filled_order.average_price}")
        self._safety_order_count += 1
        self._position_size += filled_order.quantity
        
        # Update average entry price (weighted average would be more accurate)
        if filled_order.average_price and self._entry_price:
            # Simplified average calculation (should track total quantity and cost)
            self._entry_price = (self._entry_price + filled_order.average_price) / Decimal("2")
        
        # Cancel and replace take profit order with new target
        if self._take_profit_order and self._take_profit_order.id:
            await self.cancel_order(self._take_profit_order.id)
        
        await self._place_take_profit_order()
        
        # Place next safety order if within limits
        if self._safety_order_count < self.dca_config.max_safety_orders:
            await self._place_safety_orders()
    
    async def _handle_take_profit_fill(self, filled_order: Order) -> None:
        """Handle take profit order fill.
        
        Args:
            filled_order: The filled take profit order
        """
        logger.info(f"DCA take profit filled at {filled_order.average_price}")
        
        # Reset DCA state
        await self._reset_dca_state()
        
        # Don't start new cycle immediately - let strategy decide
        logger.info(f"DCA cycle completed with profit of {filled_order.average_price - self._entry_price if self._entry_price else 0}")
    
    async def _place_take_profit_order(self) -> None:
        """Place take profit order."""
        if not self._entry_price or not self._base_order:
            return
        
        # Use the actual quantity from the base order, not entire balance
        base_quantity = self._base_order.quantity
        
        # Add any filled safety orders to the quantity
        for safety_order in self._safety_orders:
            if safety_order.status == OrderStatus.FILLED:
                base_quantity += safety_order.quantity
        
        # Calculate take profit price
        take_profit_multiplier = Decimal("1") + (self.dca_config.take_profit_percentage / Decimal("100"))
        take_profit_price = self._entry_price * take_profit_multiplier
        
        try:
            self._take_profit_order = await self.place_order(
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=base_quantity,
                price=take_profit_price
            )
            
            if self._take_profit_order:
                logger.info(f"Take profit order placed for {base_quantity} at {take_profit_price}")
        
        except Exception as e:
            logger.error(f"Failed to place take profit order: {e}")
    
    async def _place_safety_orders(self) -> None:
        """Place safety orders based on current state."""
        if not self._entry_price or self._safety_order_count >= self.dca_config.max_safety_orders:
            return
        
        current_price = self._market_data.price if self._market_data else None
        if not current_price:
            return
        
        # Calculate next safety order level
        deviation = self.dca_config.price_deviation_percentage / Decimal("100")
        step_multiplier = self.dca_config.safety_order_step_scale ** self._safety_order_count
        safety_price = self._entry_price * (Decimal("1") - deviation * step_multiplier)
        
        # Only place if current price is near safety level
        if current_price <= safety_price * Decimal("1.02"):  # 2% buffer
            # Calculate quantity with volume scaling
            volume_multiplier = self.dca_config.safety_order_volume_scale ** self._safety_order_count
            safety_quantity = (self.dca_config.safety_order_size * volume_multiplier) / safety_price
            
            try:
                safety_order = await self.place_order(
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    quantity=safety_quantity,
                    price=safety_price
                )
                
                if safety_order:
                    self._safety_orders.append(safety_order)
                    logger.info(f"Safety order {len(self._safety_orders)} placed at {safety_price}")
            
            except Exception as e:
                logger.error(f"Failed to place safety order: {e}")
    
    async def _check_stop_loss(self) -> None:
        """Check and execute stop loss if triggered."""
        if not self.dca_config.stop_loss_percentage or not self._entry_price:
            return
        
        current_price = self._market_data.price if self._market_data else None
        if not current_price:
            return
        
        # Calculate stop loss price
        stop_loss_multiplier = Decimal("1") - (self.dca_config.stop_loss_percentage / Decimal("100"))
        stop_loss_price = self._entry_price * stop_loss_multiplier
        
        if current_price <= stop_loss_price:
            logger.warning(f"Stop loss triggered at {current_price} (target: {stop_loss_price})")
            await self._execute_stop_loss()
    
    async def _execute_stop_loss(self) -> None:
        """Execute stop loss by selling all positions."""
        # Cancel all open orders
        await self.cancel_all_orders()
        
        # Sell all base asset
        base_asset = self.symbol.replace("USDT", "")[:3]
        base_balance = await self.get_balance(base_asset)
        
        if base_balance and base_balance.free > 0:
            try:
                await self.place_order(
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=base_balance.free
                )
                logger.info(f"Stop loss executed: sold {base_balance.free} {base_asset}")
            
            except Exception as e:
                logger.error(f"Failed to execute stop loss: {e}")
        
        # Reset DCA state
        await self._reset_dca_state()
    
    async def _reset_dca_state(self) -> None:
        """Reset DCA strategy state."""
        self._base_order = None
        self._safety_orders.clear()
        self._take_profit_order = None
        self._entry_price = None
        self._safety_order_count = 0
        self._position_size = Decimal("0")
        self._initialized = False
        
        logger.info("DCA state reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get DCA strategy status."""
        status = super().get_status()
        status.update({
            "entry_price": str(self._entry_price) if self._entry_price else None,
            "safety_orders_used": self._safety_order_count,
            "max_safety_orders": self.dca_config.max_safety_orders,
            "base_order_size": str(self.dca_config.base_order_size),
            "safety_order_size": str(self.dca_config.safety_order_size),
            "take_profit_percentage": str(self.dca_config.take_profit_percentage),
            "initialized": self._initialized,
        })
        return status
