"""Core type definitions for Passivbot."""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pydantic
from pydantic import BaseModel, Field, field_validator


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ExchangeType(str, Enum):
    """Supported exchanges."""
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    BINANCE_FUTURES = "binance_futures"
    BYBIT_FUTURES = "bybit_futures"


class StrategyType(str, Enum):
    """Trading strategy types."""
    GRID = "grid"
    DCA = "dca"
    RECURSIVE_GRID = "recursive_grid"
    NEAT_GRID = "neat_grid"


@dataclass(frozen=True)
class Symbol:
    """Trading symbol representation."""
    base: str
    quote: str
    exchange: ExchangeType
    
    def __str__(self) -> str:
        return f"{self.base}{self.quote}"
    
    @property
    def normalized(self) -> str:
        """Get normalized symbol format."""
        return f"{self.base.upper()}/{self.quote.upper()}"


@dataclass
class Price:
    """Price with precision handling."""
    value: Decimal
    precision: int = 8
    
    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Price cannot be negative")
    
    def __str__(self) -> str:
        return f"{self.value:.{self.precision}f}"
    
    def __float__(self) -> float:
        return float(self.value)


@dataclass
class Quantity:
    """Quantity with precision handling."""
    value: Decimal
    precision: int = 8
    
    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")
    
    def __str__(self) -> str:
        return f"{self.value:.{self.precision}f}"
    
    def __float__(self) -> float:
        return float(self.value)


class Order(BaseModel):
    """Trading order model."""
    id: Optional[str] = Field(default=None, description="Exchange order ID")
    client_id: str = Field(default_factory=lambda: str(uuid4()), description="Client order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Order side")
    type: OrderType = Field(..., description="Order type")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    price: Optional[Decimal] = Field(default=None, description="Order price")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    filled_quantity: Decimal = Field(default=Decimal("0"), description="Filled quantity")
    average_price: Optional[Decimal] = Field(default=None, description="Average fill price")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Order timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Validate price based on order type."""
        # Simplified validation for Pydantic v2
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity


class Position(BaseModel):
    """Trading position model."""
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Position side")
    size: Decimal = Field(..., description="Position size")
    entry_price: Decimal = Field(..., gt=0, description="Average entry price")
    mark_price: Optional[Decimal] = Field(default=None, description="Current mark price")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="Unrealized P&L")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized P&L")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Position timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class Balance(BaseModel):
    """Account balance model."""
    asset: str = Field(..., description="Asset symbol")
    free: Decimal = Field(..., ge=0, description="Available balance")
    locked: Decimal = Field(default=Decimal("0"), ge=0, description="Locked balance")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Balance timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    
    @property
    def total(self) -> Decimal:
        """Get total balance."""
        return self.free + self.locked


class Trade(BaseModel):
    """Trade execution model."""
    id: str = Field(..., description="Trade ID")
    order_id: str = Field(..., description="Related order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Trade side")
    quantity: Decimal = Field(..., gt=0, description="Trade quantity")
    price: Decimal = Field(..., gt=0, description="Trade price")
    fee: Decimal = Field(default=Decimal("0"), description="Trading fee")
    fee_asset: str = Field(default="", description="Fee asset")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Trade timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    
    @property
    def notional_value(self) -> Decimal:
        """Get notional value of the trade."""
        return self.quantity * self.price


class MarketData(BaseModel):
    """Market data model."""
    symbol: str = Field(..., description="Trading symbol")
    price: Decimal = Field(..., gt=0, description="Current price")
    bid: Optional[Decimal] = Field(default=None, description="Best bid price")
    ask: Optional[Decimal] = Field(default=None, description="Best ask price")
    volume_24h: Optional[Decimal] = Field(default=None, description="24h volume")
    change_24h: Optional[Decimal] = Field(default=None, description="24h price change %")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Get bid-ask spread."""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None