# Passivbot v2.0 - Refactored (Phase 1 Complete ✅)

A modern, refactored version of Passivbot with improved code readability, maintainability, and developer experience.

**🎉 Phase 1 Implementation Complete!**

## ✅ **Phase 1 Features Implemented**

- **✅ Core Bot Class**: Main PassivBot class with lifecycle management
- **✅ CLI Interface Structure**: Command-line interface with typer (requires installation)
- **✅ Exchange Abstraction**: Base exchange interface with Binance/Bybit implementations
- **✅ Strategy Framework**: Base strategy class with Grid and DCA strategy implementations
- **✅ Configuration System**: Comprehensive Pydantic-based configuration with validation
- **✅ Type System**: Complete type definitions with Pydantic models
- **✅ Exception Handling**: Hierarchical exception system with error handling utilities

## 🎯 Phase 1 Implementation Status

### ✅ **Completed Components**

#### **Core Bot System**
- `src/passivbot/__init__.py` - Main PassivBot class with async lifecycle management
- Bot status monitoring and graceful shutdown
- Strategy and exchange management
- Risk management integration

#### **CLI Interface** 
- `src/passivbot/cli.py` - Complete command-line interface
- Commands: `init`, `validate`, `run`, `status`, `web`, `version`
- Rich formatting and interactive prompts
- Configuration file management

#### **Exchange Layer**
- `src/passivbot/exchanges/` - Exchange abstraction with base interface
- `base.py` - Abstract base class with common functionality
- `binance.py` - Binance spot/futures implementation (partial)
- `bybit.py` - Bybit implementation (basic structure)
- Rate limiting and error handling

#### **Strategy Framework**
- `src/passivbot/strategies/` - Strategy system with base class
- `base.py` - Abstract strategy interface with common methods
- `grid.py` - Complete grid trading strategy implementation
- `dca.py` - Complete DCA strategy implementation
- Order management and position tracking

#### **Configuration System**
- `src/passivbot/core/config.py` - Pydantic-based configuration
- Environment variable support
- Validation with warnings/errors
- JSON file support with templates

#### **Type System**
- `src/passivbot/core/types.py` - Complete domain models
- Order, Position, Balance, Trade, MarketData models
- Enum definitions for sides, types, statuses
- Decimal precision handling

#### **Exception Handling**
- `src/passivbot/core/exceptions.py` - Hierarchical exception system
- Specific exceptions for different error types
- Error handling utilities and retry logic

### 🔧 **Next Phase Requirements**

#### **Phase 2: Exchange Integration**
- Complete Binance API authentication and signatures
- WebSocket connections for real-time data
- Order execution and management
- Balance and position updates

#### **Phase 3: Supporting Systems**
- Database layer with SQLAlchemy models
- Web interface with FastAPI
- Notification system (Telegram, Discord, Email)
- Comprehensive testing suite

#### **Phase 4: Advanced Features**
- Backtesting framework
- Performance analytics
- Portfolio management
- Advanced risk management

## 🚀 Features

- **Modern Python Architecture**: Built with Python 3.9+ and modern best practices
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Robust Configuration**: Pydantic-based configuration with validation
- **Professional Error Handling**: Specific exception types for different error conditions
- **Comprehensive Testing**: Full test coverage with pytest
- **Clean Code**: Self-documenting code with clear naming conventions

## 📦 Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/manhngodh/pv2.git
cd pv2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Production Installation

```bash
pip install passivbot
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

### Configuration File

Create a configuration file using the provided template:

```python
from passivbot.core.config import create_default_config
import json

# Create default configuration
config = create_default_config()

# Save to file
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

## 🚀 Quick Start

```python
from passivbot.core.config import PassivbotConfig
from passivbot import PassivBot

# Load configuration
config = PassivbotConfig.from_file('config.json')

# Create and run bot
bot = PassivBot(config)
await bot.start()
```

## 📊 Strategies

### Grid Trading

```python
grid_config = {
    "type": "grid",
    "symbol": "BTCUSDT",
    "grid_config": {
        "num_levels": 10,
        "quantity_percentage": 10.0,
        "price_spacing_percentage": 0.5,
        "upper_price": 50000.0,
        "lower_price": 30000.0
    }
}
```

### DCA (Dollar Cost Averaging)

```python
dca_config = {
    "type": "dca",
    "symbol": "ETHUSDT",
    "dca_config": {
        "base_order_size": 100.0,
        "safety_order_size": 50.0,
        "max_safety_orders": 5,
        "price_deviation_percentage": 2.0,
        "take_profit_percentage": 1.5
    }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/passivbot

# Run specific test file
pytest tests/test_config.py
```

## 🧪 Phase 1 Testing

Test the current implementation:

```bash
# Install basic dependencies
pip install pydantic pydantic-settings aiohttp

# Run Phase 1 test
python test_phase1.py
```

For full CLI functionality, install additional dependencies:

```bash
# Install CLI dependencies  
pip install typer rich uvicorn

# Test CLI commands
python -m src.passivbot.cli --help
python -m src.passivbot.cli init
python -m src.passivbot.cli validate
```

## 🔍 Code Quality

```bash
# Format code
black src/ tests/

# Sort imports  
isort src/ tests/

# Type checking
mypy src/

# Linting
ruff src/ tests/
```

## 📈 Monitoring

Access the web interface at `http://localhost:8080` to monitor your trading activities.

## 📚 Documentation & Architecture

### 🎨 Visual Architecture
All system diagrams and architectural documentation are organized in the [`docs/diagrams/`](./docs/diagrams/) folder:

- **[📊 Interactive Diagrams](./docs/diagrams/diagrams.html)** - Open in browser for interactive exploration
- **[🏗️ Complete Architecture Guide](./docs/diagrams/ARCHITECTURE.md)** - Comprehensive system documentation
- **[⚡ Quick Reference](./docs/diagrams/QUICK_REFERENCE.md)** - Simplified flowcharts and overview
- **[🏛️ C4 Architecture Model](./docs/diagrams/C4_ARCHITECTURE.md)** - Structured architecture views
- **[📋 Diagram Index](./docs/diagrams/index.md)** - Easy navigation to all diagrams

### 🔍 Component Documentation
Individual component diagrams are available for detailed understanding:
1. System Architecture - High-level overview
2. Bot Lifecycle - Startup to shutdown processes  
3. Configuration System - Config loading and validation
4. Exchange Layer - API abstraction and integration
5. Grid Strategy - Grid trading strategy logic
6. DCA Strategy - Dollar cost averaging implementation
7. Risk Management - Risk controls and position management
8. Data Models - Core data structures and relationships

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. Always test strategies in a simulated environment before using real funds.

## 🙏 Acknowledgments

- Original Passivbot project and contributors
- The Python trading community
- All contributors to this refactored version