"""Exchange implementations for Passivbot."""

from typing import Dict, Type
from .base import BaseExchange
from .binance import BinanceExchange
from .bybit import BybitExchange
from ..core.types import ExchangeType
from ..core.config import ExchangeConfig


# Registry of available exchanges
EXCHANGE_REGISTRY: Dict[ExchangeType, Type[BaseExchange]] = {
    ExchangeType.BINANCE: BinanceExchange,
    ExchangeType.BINANCE_FUTURES: BinanceExchange,
    ExchangeType.BYBIT: BybitExchange,
    ExchangeType.BYBIT_FUTURES: BybitExchange,
    # ExchangeType.OKX: OKXExchange,  # Will be implemented later
}


def get_exchange(config: ExchangeConfig) -> BaseExchange:
    """Get exchange instance based on configuration.
    
    Args:
        config: Exchange configuration
        
    Returns:
        Exchange instance
        
    Raises:
        ValueError: If exchange type is not supported
    """
    exchange_class = EXCHANGE_REGISTRY.get(config.type)
    
    if exchange_class is None:
        supported = ", ".join(EXCHANGE_REGISTRY.keys())
        raise ValueError(f"Unsupported exchange: {config.type}. Supported: {supported}")
    
    return exchange_class(config)


def list_supported_exchanges() -> list[ExchangeType]:
    """Get list of supported exchanges.
    
    Returns:
        List of supported exchange types
    """
    return list(EXCHANGE_REGISTRY.keys())


__all__ = [
    "get_exchange",
    "list_supported_exchanges",
    "BaseExchange",
    "BinanceExchange",
    "BybitExchange",
]
