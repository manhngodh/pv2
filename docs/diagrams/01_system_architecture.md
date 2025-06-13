# System Architecture Overview

```mermaid
graph TB
    CLI[CLI Interface<br/>typer + rich] --> Bot[PassivBot<br/>Main Controller]
    Config[Configuration<br/>Pydantic Models] --> Bot
    
    Bot --> EM[Exchange Manager]
    Bot --> SM[Strategy Manager] 
    Bot --> RM[Risk Manager]
    Bot --> Web[Web Interface<br/>FastAPI]
    
    EM --> Binance[Binance Exchange]
    EM --> Bybit[Bybit Exchange]
    EM --> OKX[OKX Exchange<br/>Future]
    
    SM --> Grid[Grid Strategy]
    SM --> DCA[DCA Strategy]
    SM --> Custom[Custom Strategies<br/>Future]
    
    RM --> Position[Position Monitor]
    RM --> Drawdown[Drawdown Check]
    RM --> Stop[Emergency Stop]
    
    Bot --> DB[(Database<br/>SQLAlchemy)]
    Bot --> Notify[Notifications<br/>Telegram/Discord]
    
    style Bot fill:#e1f5fe
    style EM fill:#f3e5f5
    style SM fill:#e8f5e8
    style RM fill:#fff3e0
```

## Components Description

### Core Components
- **PassivBot**: Main controller orchestrating all operations
- **CLI Interface**: Command-line interface using typer and rich for user interaction
- **Configuration**: Pydantic-based configuration management with validation

### Managers
- **Exchange Manager**: Handles all exchange connections and API interactions
- **Strategy Manager**: Manages trading strategy execution and lifecycle
- **Risk Manager**: Monitors and enforces risk management rules

### Exchange Layer
- **Binance Exchange**: Implementation for Binance spot and futures trading
- **Bybit Exchange**: Implementation for Bybit trading platform
- **OKX Exchange**: Future implementation for OKX platform

### Strategy Layer
- **Grid Strategy**: Grid trading algorithm implementation
- **DCA Strategy**: Dollar Cost Averaging strategy implementation
- **Custom Strategies**: Extensible framework for additional strategies

### Supporting Systems
- **Database**: SQLAlchemy-based data persistence layer
- **Web Interface**: FastAPI-based web dashboard (future implementation)
- **Notifications**: Multi-channel notification system
