# Configuration System Structure

```mermaid
classDiagram
    class PassivbotConfig {
        +LogLevel log_level
        +bool dry_run
        +ExchangeConfig exchange
        +List[StrategyConfig] strategies
        +RiskConfig risk
        +DatabaseConfig database
        +WebConfig web
        +NotificationConfig notifications
        
        +from_file(path) PassivbotConfig
        +save_to_file(path) void
        +validate_strategies() void
    }
    
    class ExchangeConfig {
        +ExchangeType type
        +str api_key
        +str api_secret
        +Optional[str] passphrase
        +bool testnet
        +int rate_limit
    }
    
    class StrategyConfig {
        +StrategyType type
        +str symbol
        +bool enabled
        +Optional[GridConfig] grid_config
        +Optional[DCAConfig] dca_config
    }
    
    class GridConfig {
        +int num_levels
        +Decimal quantity_percentage
        +Decimal price_spacing_percentage
        +Optional[Decimal] upper_price
        +Optional[Decimal] lower_price
        +Decimal rebalance_threshold
    }
    
    class DCAConfig {
        +Decimal base_order_size
        +Decimal safety_order_size
        +int max_safety_orders
        +Decimal price_deviation_percentage
        +Decimal take_profit_percentage
    }
    
    class RiskConfig {
        +Decimal max_position_size
        +Decimal max_total_exposure
        +Decimal max_drawdown_percentage
        +int max_orders_per_symbol
        +bool emergency_stop
    }
    
    PassivbotConfig --> ExchangeConfig
    PassivbotConfig --> StrategyConfig
    PassivbotConfig --> RiskConfig
    StrategyConfig --> GridConfig
    StrategyConfig --> DCAConfig
```

## Configuration Hierarchy

### Main Configuration (`PassivbotConfig`)
- **Global Settings**: Log level, dry run mode
- **Component Configs**: Exchange, strategies, risk management
- **System Configs**: Database, web interface, notifications

### Exchange Configuration (`ExchangeConfig`)
- **Connection Details**: API credentials and endpoints
- **Operational Settings**: Testnet mode, rate limiting
- **Security**: API key encryption support

### Strategy Configuration (`StrategyConfig`)
- **Strategy Selection**: Type and symbol specification
- **Strategy-Specific Settings**: Grid or DCA parameters
- **Control Settings**: Enable/disable individual strategies

### Risk Management (`RiskConfig`)
- **Position Limits**: Maximum position size and exposure
- **Safety Controls**: Drawdown limits and emergency stops
- **Order Management**: Maximum orders per symbol

## Configuration Features

### Validation
- **Type Checking**: Pydantic-based type validation
- **Business Rules**: Cross-field validation and constraints
- **Warning System**: Non-critical configuration warnings

### File Support
- **JSON Format**: Human-readable configuration files
- **Environment Variables**: Override settings via .env files
- **Template Generation**: Default configuration creation

### Security
- **API Key Protection**: Secure storage recommendations
- **Testnet Support**: Safe testing environment
- **Dry Run Mode**: Risk-free strategy testing
