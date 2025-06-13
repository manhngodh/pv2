"""Custom exceptions for Passivbot."""

from typing import Optional, Any, Dict
from decimal import Decimal


class PassivbotError(Exception):
    """Base exception for all Passivbot errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(PassivbotError):
    """Configuration-related errors."""
    pass


class ExchangeError(PassivbotError):
    """Exchange-related errors."""
    pass


class ExchangeConnectionError(ExchangeError):
    """Exchange connection errors."""
    pass


class ExchangeAPIError(ExchangeError):
    """Exchange API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code
        self.error_code = error_code


class InsufficientBalanceError(ExchangeError):
    """Insufficient balance for trading."""
    
    def __init__(
        self, 
        required_balance: Decimal, 
        available_balance: Decimal, 
        asset: str
    ) -> None:
        message = (
            f"Insufficient {asset} balance. "
            f"Required: {required_balance}, Available: {available_balance}"
        )
        details = {
            "required_balance": str(required_balance),
            "available_balance": str(available_balance),
            "asset": asset
        }
        super().__init__(message, details)
        self.required_balance = required_balance
        self.available_balance = available_balance
        self.asset = asset


class OrderError(PassivbotError):
    """Order-related errors."""
    pass


class InvalidOrderError(OrderError):
    """Invalid order parameters."""
    pass


class OrderNotFoundError(OrderError):
    """Order not found."""
    
    def __init__(self, order_id: str) -> None:
        message = f"Order not found: {order_id}"
        super().__init__(message, {"order_id": order_id})
        self.order_id = order_id


class OrderRejectedError(OrderError):
    """Order rejected by exchange."""
    
    def __init__(self, reason: str, order_id: Optional[str] = None) -> None:
        message = f"Order rejected: {reason}"
        details = {"reason": reason}
        if order_id:
            details["order_id"] = order_id
        super().__init__(message, details)
        self.reason = reason
        self.order_id = order_id


class StrategyError(PassivbotError):
    """Strategy-related errors."""
    pass


class InvalidStrategyError(StrategyError):
    """Invalid strategy configuration."""
    pass


class StrategyExecutionError(StrategyError):
    """Strategy execution error."""
    pass


class RiskManagementError(PassivbotError):
    """Risk management errors."""
    pass


class MaxPositionSizeExceededError(RiskManagementError):
    """Maximum position size exceeded."""
    
    def __init__(self, current_size: Decimal, max_size: Decimal, symbol: str) -> None:
        message = (
            f"Maximum position size exceeded for {symbol}. "
            f"Current: {current_size}, Maximum: {max_size}"
        )
        details = {
            "current_size": str(current_size),
            "max_size": str(max_size),
            "symbol": symbol
        }
        super().__init__(message, details)
        self.current_size = current_size
        self.max_size = max_size
        self.symbol = symbol


class MaxDrawdownExceededError(RiskManagementError):
    """Maximum drawdown exceeded."""
    
    def __init__(self, current_drawdown: Decimal, max_drawdown: Decimal) -> None:
        message = (
            f"Maximum drawdown exceeded. "
            f"Current: {current_drawdown}%, Maximum: {max_drawdown}%"
        )
        details = {
            "current_drawdown": str(current_drawdown),
            "max_drawdown": str(max_drawdown)
        }
        super().__init__(message, details)
        self.current_drawdown = current_drawdown
        self.max_drawdown = max_drawdown


class DataError(PassivbotError):
    """Data-related errors."""
    pass


class DatabaseError(DataError):
    """Database-related errors."""
    pass


class ValidationError(PassivbotError):
    """Data validation errors."""
    pass


class InvalidPriceError(ValidationError):
    """Invalid price value."""
    
    def __init__(self, price: Any, reason: str = "Invalid price") -> None:
        message = f"{reason}: {price}"
        super().__init__(message, {"price": str(price), "reason": reason})
        self.price = price
        self.reason = reason


class InvalidQuantityError(ValidationError):
    """Invalid quantity value."""
    
    def __init__(self, quantity: Any, reason: str = "Invalid quantity") -> None:
        message = f"{reason}: {quantity}"
        super().__init__(message, {"quantity": str(quantity), "reason": reason})
        self.quantity = quantity
        self.reason = reason


class BacktestError(PassivbotError):
    """Backtesting-related errors."""
    pass


class InsufficientDataError(BacktestError):
    """Insufficient data for backtesting."""
    pass


class NotificationError(PassivbotError):
    """Notification-related errors."""
    pass


class WebInterfaceError(PassivbotError):
    """Web interface errors."""
    pass


# Error handling utilities
def handle_exchange_error(error: Exception) -> ExchangeError:
    """Convert generic exchange errors to specific PassivBot exceptions."""
    if isinstance(error, ExchangeError):
        return error
    
    error_message = str(error)
    
    # Common error patterns
    if "insufficient" in error_message.lower() and "balance" in error_message.lower():
        return InsufficientBalanceError(
            required_balance=Decimal("0"),
            available_balance=Decimal("0"),
            asset="unknown"
        )
    
    if "connection" in error_message.lower() or "timeout" in error_message.lower():
        return ExchangeConnectionError(f"Connection error: {error_message}")
    
    if "api" in error_message.lower() or "rate limit" in error_message.lower():
        return ExchangeAPIError(f"API error: {error_message}")
    
    return ExchangeError(f"Exchange error: {error_message}")


def is_retriable_error(error: Exception) -> bool:
    """Check if an error is retriable."""
    retriable_errors = (
        ExchangeConnectionError,
        ExchangeAPIError,
        DatabaseError,
    )
    
    if isinstance(error, retriable_errors):
        return True
    
    # Check error message for retriable patterns
    error_message = str(error).lower()
    retriable_patterns = [
        "timeout",
        "connection",
        "rate limit",
        "server error",
        "service unavailable",
        "temporary",
    ]
    
    return any(pattern in error_message for pattern in retriable_patterns)