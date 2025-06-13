"""Configuration management for Passivbot."""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import json
import os
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from .types import ExchangeType, StrategyType, OrderSide


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExchangeConfig(BaseModel):
    """Exchange configuration."""
    type: ExchangeType = Field(..., description="Exchange type")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    passphrase: Optional[str] = Field(default=None, description="Passphrase (for OKX)")
    testnet: bool = Field(default=False, description="Use testnet")
    rate_limit: int = Field(default=10, description="API rate limit per second")
    
    class Config:
        use_enum_values = True


class GridConfig(BaseModel):
    """Grid trading strategy configuration."""
    num_levels: int = Field(..., gt=0, le=100, description="Number of grid levels")
    quantity_percentage: Decimal = Field(
        ..., gt=0, le=100, description="Percentage of balance per level"
    )
    price_spacing_percentage: Decimal = Field(
        ..., gt=0, le=50, description="Price spacing between levels (%)"
    )
    upper_price: Optional[Decimal] = Field(
        default=None, gt=0, description="Upper grid boundary"
    )
    lower_price: Optional[Decimal] = Field(
        default=None, gt=0, description="Lower grid boundary"
    )
    rebalance_threshold: Decimal = Field(
        default=Decimal("5.0"), gt=0, description="Rebalance threshold (%)"
    )
    
    @field_validator('lower_price')
    @classmethod
    def validate_price_bounds(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Validate price boundaries."""
        # In Pydantic v2, we need to access other field values differently
        # This is a simplified version - full implementation would need model_validator
        if v is not None and v <= 0:
            raise ValueError("Lower price must be positive")
        return v
    
    @property
    def has_boundaries(self) -> bool:
        """Check if grid has defined boundaries."""
        return self.upper_price is not None and self.lower_price is not None


class DCAConfig(BaseModel):
    """DCA (Dollar Cost Averaging) strategy configuration."""
    base_order_size: Decimal = Field(..., gt=0, description="Base order size")
    safety_order_size: Decimal = Field(..., gt=0, description="Safety order size")
    max_safety_orders: int = Field(..., gt=0, le=50, description="Maximum safety orders")
    price_deviation_percentage: Decimal = Field(
        ..., gt=0, le=50, description="Price deviation to trigger safety order (%)"
    )
    safety_order_step_scale: Decimal = Field(
        default=Decimal("1.0"), gt=0, description="Safety order step scale"
    )
    safety_order_volume_scale: Decimal = Field(
        default=Decimal("1.0"), gt=0, description="Safety order volume scale"
    )
    take_profit_percentage: Decimal = Field(
        default=Decimal("1.0"), gt=0, description="Take profit percentage"
    )
    stop_loss_percentage: Optional[Decimal] = Field(
        default=None, gt=0, description="Stop loss percentage"
    )


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_position_size: Decimal = Field(
        default=Decimal("1000.0"), gt=0, description="Maximum position size"
    )
    max_total_exposure: Decimal = Field(
        default=Decimal("10000.0"), gt=0, description="Maximum total exposure"
    )
    max_drawdown_percentage: Decimal = Field(
        default=Decimal("20.0"), gt=0, le=100, description="Maximum drawdown (%)"
    )
    stop_loss_percentage: Optional[Decimal] = Field(
        default=None, gt=0, description="Global stop loss (%)"
    )
    max_orders_per_symbol: int = Field(
        default=10, gt=0, description="Maximum orders per symbol"
    )
    emergency_stop: bool = Field(
        default=False, description="Emergency stop all trading"
    )


class StrategyConfig(BaseModel):
    """Strategy configuration."""
    type: StrategyType = Field(..., description="Strategy type")
    symbol: str = Field(..., description="Trading symbol")
    enabled: bool = Field(default=True, description="Strategy enabled")
    grid_config: Optional[GridConfig] = Field(default=None, description="Grid configuration")
    dca_config: Optional[DCAConfig] = Field(default=None, description="DCA configuration")
    
    class Config:
        use_enum_values = True
    
    @model_validator(mode='after')
    def validate_strategy_config(self) -> 'StrategyConfig':
        """Validate strategy-specific configuration."""
        if self.type == StrategyType.GRID and self.grid_config is None:
            raise ValueError("Grid configuration required for grid strategy")
        if self.type == StrategyType.DCA and self.dca_config is None:
            raise ValueError("DCA configuration required for DCA strategy")
            
        return self


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///passivbot.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")


class WebConfig(BaseModel):
    """Web interface configuration."""
    enabled: bool = Field(default=True, description="Enable web interface")
    host: str = Field(default="127.0.0.1", description="Web server host")
    port: int = Field(default=8080, description="Web server port")
    debug: bool = Field(default=False, description="Enable debug mode")


class NotificationConfig(BaseModel):
    """Notification configuration."""
    enabled: bool = Field(default=False, description="Enable notifications")
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID")
    discord_webhook_url: Optional[str] = Field(default=None, description="Discord webhook URL")
    email_smtp_server: Optional[str] = Field(default=None, description="SMTP server")
    email_username: Optional[str] = Field(default=None, description="Email username")
    email_password: Optional[str] = Field(default=None, description="Email password")
    email_recipients: List[str] = Field(default_factory=list, description="Email recipients")


class PassivbotConfig(BaseSettings):
    """Main Passivbot configuration."""
    
    # General settings
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    dry_run: bool = Field(default=False, description="Dry run mode (no real trading)")
    
    # Exchange settings
    exchange: ExchangeConfig = Field(..., description="Exchange configuration")
    
    # Strategy settings
    strategies: List[StrategyConfig] = Field(..., description="Trading strategies")
    
    # Risk management
    risk: RiskConfig = Field(default_factory=RiskConfig, description="Risk configuration")
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database config")
    
    # Web interface
    web: WebConfig = Field(default_factory=WebConfig, description="Web interface config")
    
    # Notifications
    notifications: NotificationConfig = Field(
        default_factory=NotificationConfig, description="Notification config"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        use_enum_values = True
        case_sensitive = False
        
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "PassivbotConfig":
        """Load configuration from file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        return cls(**data)
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                json.dump(self.dict(), f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    def validate_strategies(self) -> None:
        """Validate all strategy configurations."""
        if not self.strategies:
            raise ValueError("At least one strategy must be configured")
        
        symbols = [strategy.symbol for strategy in self.strategies]
        if len(symbols) != len(set(symbols)):
            raise ValueError("Duplicate symbols in strategy configuration")


# Configuration validation functions
def validate_configuration(config: PassivbotConfig) -> List[str]:
    """Validate configuration and return list of warnings/errors."""
    warnings = []
    
    # Validate exchange configuration
    if config.exchange.testnet and not config.dry_run:
        warnings.append("Using testnet but dry_run is disabled")
    
    # Validate strategies
    try:
        config.validate_strategies()
    except ValueError as e:
        warnings.append(f"Strategy validation error: {e}")
    
    # Validate risk settings
    if config.risk.max_drawdown_percentage > 50:
        warnings.append("High maximum drawdown percentage (>50%)")
    
    # Validate notification settings
    if config.notifications.enabled:
        if not any([
            config.notifications.telegram_bot_token,
            config.notifications.discord_webhook_url,
            config.notifications.email_smtp_server
        ]):
            warnings.append("Notifications enabled but no notification method configured")
    
    return warnings


# Default configuration template
def create_default_config() -> Dict[str, Any]:
    """Create a default configuration template."""
    return {
        "log_level": "INFO",
        "dry_run": True,
        "exchange": {
            "type": "binance",
            "api_key": "your_api_key_here",
            "api_secret": "your_api_secret_here",
            "testnet": True,
            "rate_limit": 10
        },
        "strategies": [
            {
                "type": "grid",
                "symbol": "BTCUSDT",
                "enabled": True,
                "grid_config": {
                    "num_levels": 10,
                    "quantity_percentage": 10.0,
                    "price_spacing_percentage": 0.5,
                    "rebalance_threshold": 5.0
                }
            }
        ],
        "risk": {
            "max_position_size": 1000.0,
            "max_total_exposure": 10000.0,
            "max_drawdown_percentage": 20.0,
            "max_orders_per_symbol": 10,
            "emergency_stop": False
        },
        "database": {
            "url": "sqlite:///passivbot.db",
            "echo": False
        },
        "web": {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 8080,
            "debug": False
        },
        "notifications": {
            "enabled": False
        }
    }