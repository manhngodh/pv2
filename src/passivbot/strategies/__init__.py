"""Trading strategies for Passivbot."""

from typing import Dict, Type
from .base import BaseStrategy
from .grid import GridStrategy
from .dca import DCAStrategy
from ..core.types import StrategyType
from ..core.config import StrategyConfig
from ..exchanges.base import BaseExchange


# Registry of available strategies
STRATEGY_REGISTRY: Dict[StrategyType, Type[BaseStrategy]] = {
    StrategyType.GRID: GridStrategy,
    StrategyType.DCA: DCAStrategy,
    # StrategyType.RECURSIVE_GRID: RecursiveGridStrategy,  # Will be implemented later
    # StrategyType.NEAT_GRID: NeatGridStrategy,  # Will be implemented later
}


def get_strategy(
    config: StrategyConfig, 
    exchange: BaseExchange, 
    dry_run: bool = False
) -> BaseStrategy:
    """Get strategy instance based on configuration.
    
    Args:
        config: Strategy configuration
        exchange: Exchange instance
        dry_run: Whether to run in dry mode
        
    Returns:
        Strategy instance
        
    Raises:
        ValueError: If strategy type is not supported
    """
    strategy_class = STRATEGY_REGISTRY.get(config.type)
    
    if strategy_class is None:
        supported = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Unsupported strategy: {config.type}. Supported: {supported}")
    
    return strategy_class(config, exchange, dry_run)


def list_supported_strategies() -> list[StrategyType]:
    """Get list of supported strategies.
    
    Returns:
        List of supported strategy types
    """
    return list(STRATEGY_REGISTRY.keys())


__all__ = [
    "get_strategy",
    "list_supported_strategies",
    "BaseStrategy",
    "GridStrategy",
    "DCAStrategy",
]
