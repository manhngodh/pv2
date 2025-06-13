"""Passivbot - Advanced cryptocurrency trading bot."""

from decimal import Decimal
from typing import Dict, List, Optional, AsyncContextManager
import asyncio
import logging
from datetime import datetime

from .core.config import PassivbotConfig
from .core.types import Balance, Position, Order, OrderStatus
from .core.exceptions import (
    PassivbotError, 
    ExchangeError, 
    RiskManagementError,
    MaxDrawdownExceededError
)

__version__ = "2.0.0"
__author__ = "Passivbot Contributors"

logger = logging.getLogger(__name__)


class PassivBot:
    """Main Passivbot trading bot class."""
    
    def __init__(self, config: PassivbotConfig) -> None:
        """Initialize the trading bot.
        
        Args:
            config: Bot configuration
        """
        self.config = config
        self.is_running = False
        self._exchange = None
        self._strategies: List = []
        self._positions: Dict[str, Position] = {}
        self._balances: Dict[str, Balance] = {}
        self._orders: Dict[str, Order] = {}
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Passivbot v{__version__} initialized")
        if config.dry_run:
            logger.warning("Running in DRY RUN mode - no real trades will be executed")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.value),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                *([logging.FileHandler(self.config.log_file)] if self.config.log_file else [])
            ]
        )
    
    async def start(self) -> None:
        """Start the trading bot."""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        try:
            logger.info("Starting Passivbot...")
            
            # Initialize exchange connection
            await self._initialize_exchange()
            
            # Initialize strategies
            await self._initialize_strategies()
            
            # Start main trading loop
            self.is_running = True
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the trading bot."""
        if not self.is_running:
            return
        
        logger.info("Stopping Passivbot...")
        self.is_running = False
        
        # Cancel all open orders if not dry run
        if not self.config.dry_run:
            await self._cancel_all_orders()
        
        # Cleanup strategies
        for strategy in self._strategies:
            if hasattr(strategy, 'cleanup'):
                await strategy.cleanup()
        
        # Close exchange connection
        if self._exchange:
            await self._exchange.close()
        
        logger.info("Passivbot stopped")
    
    async def _initialize_exchange(self) -> None:
        """Initialize exchange connection."""
        # Import here to avoid circular imports
        from .exchanges import get_exchange
        
        self._exchange = get_exchange(self.config.exchange)
        await self._exchange.connect()
        logger.info(f"Connected to {self.config.exchange.type} exchange")
    
    async def _initialize_strategies(self) -> None:
        """Initialize trading strategies."""
        from .strategies import get_strategy
        
        for strategy_config in self.config.strategies:
            if not strategy_config.enabled:
                logger.info(f"Skipping disabled strategy: {strategy_config.symbol}")
                continue
            
            strategy = get_strategy(strategy_config, self._exchange, self.config.dry_run)
            self._strategies.append(strategy)
            logger.info(f"Initialized {strategy_config.type} strategy for {strategy_config.symbol}")
    
    async def _main_loop(self) -> None:
        """Main trading loop."""
        logger.info("Starting main trading loop")
        
        while self.is_running:
            try:
                # Update account data
                await self._update_account_data()
                
                # Check risk management
                await self._check_risk_management()
                
                # Execute strategies
                for strategy in self._strategies:
                    if self.is_running:
                        await strategy.execute()
                
                # Wait before next iteration
                await asyncio.sleep(1)  # 1 second loop
                
            except RiskManagementError as e:
                logger.error(f"Risk management error: {e}")
                if isinstance(e, MaxDrawdownExceededError):
                    logger.critical("Maximum drawdown exceeded - stopping bot")
                    await self.stop()
                    break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _update_account_data(self) -> None:
        """Update account balances and positions."""
        try:
            # Update balances
            balances = await self._exchange.get_balances()
            self._balances.update({b.asset: b for b in balances})
            
            # Update positions
            positions = await self._exchange.get_positions()
            self._positions.update({p.symbol: p for p in positions})
            
        except ExchangeError as e:
            logger.warning(f"Failed to update account data: {e}")
    
    async def _check_risk_management(self) -> None:
        """Check risk management rules."""
        # Check emergency stop
        if self.config.risk.emergency_stop:
            raise RiskManagementError("Emergency stop activated")
        
        # Check maximum drawdown
        current_drawdown = await self._calculate_drawdown()
        if current_drawdown > self.config.risk.max_drawdown_percentage:
            raise MaxDrawdownExceededError(current_drawdown, self.config.risk.max_drawdown_percentage)
    
    async def _calculate_drawdown(self) -> Decimal:
        """Calculate current portfolio drawdown."""
        # Simplified drawdown calculation
        # In real implementation, this would track historical peak values
        total_value = sum(balance.total for balance in self._balances.values())
        # For now, return 0 as we don't have historical data
        return Decimal("0")
    
    async def _cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        open_orders = [order for order in self._orders.values() 
                      if order.status in [OrderStatus.OPEN, OrderStatus.PENDING]]
        
        for order in open_orders:
            try:
                await self._exchange.cancel_order(order.id, order.symbol)
                logger.info(f"Cancelled order {order.id}")
            except Exception as e:
                logger.error(f"Failed to cancel order {order.id}: {e}")
    
    @property
    def status(self) -> Dict:
        """Get bot status information."""
        return {
            "running": self.is_running,
            "dry_run": self.config.dry_run,
            "exchange": self.config.exchange.type,
            "strategies": len(self._strategies),
            "positions": len(self._positions),
            "orders": len([o for o in self._orders.values() 
                          if o.status in [OrderStatus.OPEN, OrderStatus.PENDING]])
        }


# Context manager for bot lifecycle
class BotManager:
    """Context manager for bot lifecycle management."""
    
    def __init__(self, config: PassivbotConfig) -> None:
        self.config = config
        self.bot: Optional[PassivBot] = None
    
    async def __aenter__(self) -> PassivBot:
        """Enter the context manager."""
        self.bot = PassivBot(self.config)
        return self.bot
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        if self.bot:
            await self.bot.stop()


# Convenience functions
async def create_bot(config_path: str) -> PassivBot:
    """Create a bot from configuration file."""
    config = PassivbotConfig.from_file(config_path)
    return PassivBot(config)


async def run_bot(config_path: str) -> None:
    """Run bot from configuration file."""
    async with BotManager(PassivbotConfig.from_file(config_path)) as bot:
        await bot.start()
