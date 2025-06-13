"""Grid trading strategy implementation."""

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


class GridStrategy(BaseStrategy):
    """Grid trading strategy implementation."""
    
    def __init__(
        self, 
        config: StrategyConfig, 
        exchange: BaseExchange, 
        dry_run: bool = False
    ) -> None:
        """Initialize grid strategy.
        
        Args:
            config: Strategy configuration
            exchange: Exchange instance
            dry_run: Whether to run in dry mode
        """
        super().__init__(config, exchange, dry_run)
        
        if not config.grid_config:
            raise StrategyError("Grid configuration is required for grid strategy")
        
        self.grid_config = config.grid_config
        self._grid_levels: List[Decimal] = []
        self._buy_orders: Dict[str, Order] = {}
        self._sell_orders: Dict[str, Order] = {}
        self._initialized = False
        
        logger.info(
            f"Grid strategy initialized: {self.grid_config.num_levels} levels, "
            f"{self.grid_config.price_spacing_percentage}% spacing"
        )
    
    async def execute(self) -> None:
        """Execute grid strategy logic."""
        if not self.is_active:
            return
        
        try:
            # Update market data
            await self.update_market_data()
            await self.update_orders()
            
            if not self._market_data:
                logger.warning(f"No market data available for {self.symbol}")
                return
            
            # Initialize grid if not done
            if not self._initialized:
                await self._initialize_grid()
                self._initialized = True
            
            # Check and manage grid orders
            await self._manage_grid_orders()
            
            # Rebalance grid if needed
            await self._check_rebalancing()
            
            self._last_execution = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error executing grid strategy for {self.symbol}: {e}")
            raise StrategyExecutionError(f"Grid strategy execution failed: {e}")
    
    async def calculate_orders(self) -> List[Order]:
        """Calculate orders to place based on grid levels.
        
        Returns:
            List of orders to place
        """
        if not self._market_data or not self._grid_levels:
            return []
        
        orders = []
        current_price = self._market_data.price
        
        # Get base asset from symbol (e.g., BTC from BTCUSDT)
        base_asset = self.symbol.replace("USDT", "").replace("BTC", "").replace("ETH", "")
        if not base_asset:
            base_asset = self.symbol[:3]  # Fallback
        
        # Get balance for quantity calculation
        quote_balance = await self.get_balance("USDT")  # Assuming USDT pairs
        if not quote_balance:
            logger.warning(f"No USDT balance available for {self.symbol}")
            return []
        
        # Calculate quantity per grid level
        quantity_per_level = self.calculate_quantity_from_percentage(
            quote_balance, self.grid_config.quantity_percentage
        )
        
        for level in self._grid_levels:
            # Place buy orders below current price
            if level < current_price:
                # Calculate quantity based on level price
                level_quantity = quantity_per_level / level
                
                orders.append(Order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    type=OrderType.LIMIT,
                    quantity=level_quantity,
                    price=level,
                    status=OrderStatus.PENDING
                ))
            
            # Place sell orders above current price
            elif level > current_price:
                # For sell orders, we need base asset balance
                base_balance = await self.get_balance(base_asset)
                if base_balance and base_balance.free > 0:
                    # Calculate sell quantity
                    sell_quantity = self.calculate_quantity_from_percentage(
                        base_balance, self.grid_config.quantity_percentage
                    )
                    
                    orders.append(Order(
                        symbol=self.symbol,
                        side=OrderSide.SELL,
                        type=OrderType.LIMIT,
                        quantity=sell_quantity,
                        price=level,
                        status=OrderStatus.PENDING
                    ))
        
        return orders
    
    async def _initialize_grid(self) -> None:
        """Initialize grid levels and place initial orders."""
        if not self._market_data:
            return
        
        current_price = self._market_data.price
        
        # Calculate grid levels
        self._grid_levels = self.calculate_grid_levels(
            current_price=current_price,
            num_levels=self.grid_config.num_levels,
            spacing_percentage=self.grid_config.price_spacing_percentage,
            upper_price=self.grid_config.upper_price,
            lower_price=self.grid_config.lower_price
        )
        
        logger.info(
            f"Grid initialized with {len(self._grid_levels)} levels: "
            f"{min(self._grid_levels)} - {max(self._grid_levels)}"
        )
        
        # Place initial grid orders
        orders_to_place = await self.calculate_orders()
        
        for order in orders_to_place:
            try:
                placed_order = await self.place_order(
                    side=order.side,
                    order_type=order.type,
                    quantity=order.quantity,
                    price=order.price
                )
                
                if placed_order and placed_order.id:
                    if order.side == OrderSide.BUY:
                        self._buy_orders[placed_order.id] = placed_order
                    else:
                        self._sell_orders[placed_order.id] = placed_order
                
            except Exception as e:
                logger.warning(f"Failed to place grid order: {e}")
    
    async def _manage_grid_orders(self) -> None:
        """Manage existing grid orders and place new ones if needed."""
        # Check for filled orders and replace them
        await self._handle_filled_orders()
        
        # Ensure we have orders at all grid levels
        await self._ensure_grid_coverage()
    
    async def _handle_filled_orders(self) -> None:
        """Handle filled orders and place opposite orders."""
        all_orders = {**self._buy_orders, **self._sell_orders}
        
        for order_id, order in list(all_orders.items()):
            # Update order status
            updated_order = await self.exchange.get_order(order_id, self.symbol)
            if not updated_order:
                continue
            
            if updated_order.is_filled:
                logger.info(f"Grid order {order_id} filled at {updated_order.average_price}")
                
                # Remove from tracking
                if order_id in self._buy_orders:
                    del self._buy_orders[order_id]
                    # Place corresponding sell order
                    await self._place_opposite_order(updated_order, OrderSide.SELL)
                elif order_id in self._sell_orders:
                    del self._sell_orders[order_id]
                    # Place corresponding buy order
                    await self._place_opposite_order(updated_order, OrderSide.BUY)
    
    async def _place_opposite_order(self, filled_order: Order, side: OrderSide) -> None:
        """Place opposite order after a grid order is filled.
        
        Args:
            filled_order: The order that was filled
            side: Side of the opposite order to place
        """
        if not filled_order.average_price:
            logger.warning("Cannot place opposite order: no fill price available")
            return
        
        # Calculate opposite price with grid spacing
        spacing = self.grid_config.price_spacing_percentage / Decimal("100")
        
        if side == OrderSide.BUY:
            # Place buy order below the fill price
            opposite_price = filled_order.average_price * (Decimal("1") - spacing)
        else:
            # Place sell order above the fill price
            opposite_price = filled_order.average_price * (Decimal("1") + spacing)
        
        try:
            opposite_order = await self.place_order(
                side=side,
                order_type=OrderType.LIMIT,
                quantity=filled_order.filled_quantity,
                price=opposite_price
            )
            
            if opposite_order and opposite_order.id:
                if side == OrderSide.BUY:
                    self._buy_orders[opposite_order.id] = opposite_order
                else:
                    self._sell_orders[opposite_order.id] = opposite_order
                
                logger.info(f"Placed opposite {side.value} order at {opposite_price}")
        
        except Exception as e:
            logger.error(f"Failed to place opposite order: {e}")
    
    async def _ensure_grid_coverage(self) -> None:
        """Ensure we have orders covering all grid levels."""
        if not self._market_data:
            return
        
        current_price = self._market_data.price
        
        # Check which levels need orders
        buy_levels_needed = [level for level in self._grid_levels if level < current_price]
        sell_levels_needed = [level for level in self._grid_levels if level > current_price]
        
        # Get existing order prices
        buy_prices = {order.price for order in self._buy_orders.values()}
        sell_prices = {order.price for order in self._sell_orders.values()}
        
        # Place missing buy orders
        for level in buy_levels_needed:
            if level not in buy_prices:
                await self._place_grid_order_at_level(level, OrderSide.BUY)
        
        # Place missing sell orders
        for level in sell_levels_needed:
            if level not in sell_prices:
                await self._place_grid_order_at_level(level, OrderSide.SELL)
    
    async def _place_grid_order_at_level(self, price: Decimal, side: OrderSide) -> None:
        """Place a grid order at specific price level.
        
        Args:
            price: Price level
            side: Order side
        """
        # Calculate quantity based on configuration
        if side == OrderSide.BUY:
            quote_balance = await self.get_balance("USDT")
            if not quote_balance:
                return
            
            quantity_per_level = self.calculate_quantity_from_percentage(
                quote_balance, self.grid_config.quantity_percentage
            )
            quantity = quantity_per_level / price
        else:
            base_asset = self.symbol.replace("USDT", "")[:3]
            base_balance = await self.get_balance(base_asset)
            if not base_balance:
                return
            
            quantity = self.calculate_quantity_from_percentage(
                base_balance, self.grid_config.quantity_percentage
            )
        
        try:
            order = await self.place_order(
                side=side,
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=price
            )
            
            if order and order.id:
                if side == OrderSide.BUY:
                    self._buy_orders[order.id] = order
                else:
                    self._sell_orders[order.id] = order
        
        except Exception as e:
            logger.warning(f"Failed to place grid order at {price}: {e}")
    
    async def _check_rebalancing(self) -> None:
        """Check if grid needs rebalancing."""
        if not self._market_data or not self._grid_levels:
            return
        
        current_price = self._market_data.price
        
        # Calculate how far current price is from grid center
        grid_center = sum(self._grid_levels) / len(self._grid_levels)
        deviation = abs(current_price - grid_center) / grid_center * Decimal("100")
        
        if deviation > self.grid_config.rebalance_threshold:
            logger.info(f"Grid rebalancing triggered: {deviation}% deviation")
            await self._rebalance_grid()
    
    async def _rebalance_grid(self) -> None:
        """Rebalance the grid around current price."""
        # Cancel all existing orders
        await self.cancel_all_orders()
        
        # Clear order tracking
        self._buy_orders.clear()
        self._sell_orders.clear()
        
        # Reinitialize grid
        self._initialized = False
        await self._initialize_grid()
        
        logger.info("Grid rebalanced successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """Get grid strategy status."""
        status = super().get_status()
        status.update({
            "grid_levels": len(self._grid_levels),
            "buy_orders": len(self._buy_orders),
            "sell_orders": len(self._sell_orders),
            "spacing_percentage": str(self.grid_config.price_spacing_percentage),
            "quantity_percentage": str(self.grid_config.quantity_percentage),
            "initialized": self._initialized,
        })
        return status
