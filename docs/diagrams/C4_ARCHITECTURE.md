# Passivbot v2.0 - C4 Model Architecture

This document presents the Passivbot system architecture using the C4 model approach, showing the system at different levels of abstraction.

## Level 1: System Context Diagram

Shows how Passivbot fits into the overall environment and interacts with external systems.

```mermaid
C4Context
    title System Context Diagram - Passivbot Trading Bot

    Person(trader, "Crypto Trader", "User who configures and monitors the trading bot")
    
    System(passivbot, "Passivbot v2.0", "Automated cryptocurrency trading bot with grid and DCA strategies")
    
    System_Ext(binance, "Binance Exchange", "Cryptocurrency exchange API for trading")
    System_Ext(bybit, "Bybit Exchange", "Cryptocurrency exchange API for trading")
    System_Ext(telegram, "Telegram", "Notification service for alerts")
    System_Ext(discord, "Discord", "Notification service for alerts")
    
    Rel(trader, passivbot, "Configures strategies, monitors performance", "CLI/Web UI")
    Rel(passivbot, binance, "Places orders, gets market data", "REST API/WebSocket")
    Rel(passivbot, bybit, "Places orders, gets market data", "REST API/WebSocket")
    Rel(passivbot, telegram, "Sends notifications", "Bot API")
    Rel(passivbot, discord, "Sends notifications", "Webhook")
    
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Level 2: Container Diagram

Shows the major containers (applications, databases, etc.) that make up Passivbot.

```mermaid
C4Container
    title Container Diagram - Passivbot v2.0

    Person(trader, "Crypto Trader", "Configures and monitors trading")

    System_Boundary(c1, "Passivbot System") {
        Container(cli, "CLI Application", "Python/Typer", "Command-line interface for bot management")
        Container(web, "Web Application", "FastAPI/React", "Web dashboard for monitoring and control")
        Container(bot, "Trading Bot Core", "Python/AsyncIO", "Main trading engine with strategies")
        Container(db, "Database", "SQLite/PostgreSQL", "Stores trading history, positions, and configurations")
        Container(config, "Configuration", "JSON/YAML", "Trading strategies and risk parameters")
    }

    System_Ext(exchanges, "Crypto Exchanges", "External trading APIs")
    System_Ext(notifications, "Notification Services", "Telegram, Discord, Email")

    Rel(trader, cli, "Manages bot", "Commands")
    Rel(trader, web, "Monitors performance", "HTTPS")
    Rel(cli, bot, "Controls bot lifecycle", "Direct calls")
    Rel(web, bot, "Gets status, controls bot", "API calls")
    Rel(bot, db, "Reads/writes trading data", "SQL")
    Rel(bot, config, "Reads configuration", "File I/O")
    Rel(bot, exchanges, "Trading operations", "REST/WebSocket")
    Rel(bot, notifications, "Sends alerts", "API calls")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 3: Component Diagram - Trading Bot Core

Shows the internal components of the main trading bot container.

```mermaid
C4Component
    title Component Diagram - Trading Bot Core

    Container(web, "Web Application", "FastAPI", "Web dashboard")
    Container(cli, "CLI Application", "Python/Typer", "Command line interface")
    Container(db, "Database", "SQLite/PostgreSQL", "Data persistence")

    Container_Boundary(c1, "Trading Bot Core") {
        Component(bot_controller, "Bot Controller", "PassivBot Class", "Main orchestrator managing bot lifecycle")
        Component(config_manager, "Configuration Manager", "Pydantic Models", "Loads and validates configuration")
        Component(risk_manager, "Risk Manager", "Risk Controller", "Monitors drawdown, position sizes, and stops")
        
        Component(exchange_manager, "Exchange Manager", "Exchange Registry", "Manages exchange connections and operations")
        Component(binance_impl, "Binance Implementation", "BinanceExchange", "Binance-specific API integration")
        Component(bybit_impl, "Bybit Implementation", "BybitExchange", "Bybit-specific API integration")
        
        Component(strategy_manager, "Strategy Manager", "Strategy Registry", "Orchestrates trading strategies")
        Component(grid_strategy, "Grid Strategy", "GridStrategy Class", "Grid trading algorithm implementation")
        Component(dca_strategy, "DCA Strategy", "DCAStrategy Class", "Dollar cost averaging algorithm")
        
        Component(order_manager, "Order Manager", "Order Controller", "Manages order lifecycle and state")
        Component(position_tracker, "Position Tracker", "Position Monitor", "Tracks open positions and P&L")
        Component(market_data, "Market Data Handler", "Data Processor", "Processes real-time market data")
        Component(notification_service, "Notification Service", "Alert Manager", "Sends notifications and alerts")
    }

    System_Ext(exchanges, "External Exchanges", "Trading APIs")
    System_Ext(notifications, "External Notifications", "Telegram/Discord")

    Rel(cli, bot_controller, "Controls", "Method calls")
    Rel(web, bot_controller, "Status/Control", "API")
    Rel(bot_controller, config_manager, "Loads config", "Pydantic")
    Rel(bot_controller, risk_manager, "Risk checks", "Validation")
    Rel(bot_controller, exchange_manager, "Exchange ops", "Interface")
    Rel(bot_controller, strategy_manager, "Execute strategies", "Strategy calls")
    
    Rel(exchange_manager, binance_impl, "Binance calls", "Implementation")
    Rel(exchange_manager, bybit_impl, "Bybit calls", "Implementation")
    Rel(binance_impl, exchanges, "API calls", "REST/WS")
    Rel(bybit_impl, exchanges, "API calls", "REST/WS")
    
    Rel(strategy_manager, grid_strategy, "Execute grid", "Strategy pattern")
    Rel(strategy_manager, dca_strategy, "Execute DCA", "Strategy pattern")
    Rel(grid_strategy, order_manager, "Place orders", "Order ops")
    Rel(dca_strategy, order_manager, "Place orders", "Order ops")
    
    Rel(order_manager, exchange_manager, "Order operations", "Exchange interface")
    Rel(position_tracker, exchange_manager, "Position updates", "Data sync")
    Rel(market_data, exchange_manager, "Market updates", "WebSocket")
    Rel(notification_service, notifications, "Send alerts", "External API")
    
    Rel(bot_controller, db, "Persist data", "ORM")
    Rel(order_manager, db, "Save orders", "SQL")
    Rel(position_tracker, db, "Save positions", "SQL")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

## Level 4: Code Diagram - Grid Strategy Component

Shows the internal structure of the Grid Strategy component.

```mermaid
C4Component
    title Code Diagram - Grid Strategy Component

    Component_Ext(strategy_manager, "Strategy Manager", "Strategy orchestrator")
    Component_Ext(order_manager, "Order Manager", "Order operations")
    Component_Ext(exchange_manager, "Exchange Manager", "Market data and trading")

    Container_Boundary(c1, "Grid Strategy") {
        Component(grid_strategy, "GridStrategy", "Main Class", "Grid trading strategy implementation")
        Component(grid_calculator, "Grid Calculator", "Helper Class", "Calculates grid levels and spacing")
        Component(order_tracker, "Order Tracker", "State Manager", "Tracks buy/sell orders in grid")
        Component(rebalancer, "Grid Rebalancer", "Logic Handler", "Handles grid rebalancing logic")
        Component(fill_handler, "Fill Handler", "Event Handler", "Processes order fills and places opposite orders")
        Component(level_manager, "Level Manager", "Grid Controller", "Ensures orders at all grid levels")
    }

    Rel(strategy_manager, grid_strategy, "execute()", "Strategy interface")
    Rel(grid_strategy, grid_calculator, "calculate_grid_levels()", "Math operations")
    Rel(grid_strategy, order_tracker, "track_orders()", "State management")
    Rel(grid_strategy, rebalancer, "check_rebalancing()", "Rebalance logic")
    Rel(grid_strategy, fill_handler, "handle_filled_orders()", "Event processing")
    Rel(grid_strategy, level_manager, "ensure_grid_coverage()", "Grid maintenance")
    
    Rel(grid_strategy, order_manager, "place_order(), cancel_order()", "Order operations")
    Rel(grid_strategy, exchange_manager, "get_market_data(), get_balance()", "Market data")
    
    Rel(fill_handler, order_manager, "place_opposite_order()", "New orders")
    Rel(rebalancer, order_manager, "cancel_all_orders()", "Grid reset")
    Rel(level_manager, order_manager, "place_grid_order()", "Missing orders")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Deployment Diagram

Shows how Passivbot is deployed in different environments.

```mermaid
C4Deployment
    title Deployment Diagram - Passivbot v2.0

    Deployment_Node(user_machine, "User's Computer", "Windows/Mac/Linux") {
        Container(cli_local, "Passivbot CLI", "Python", "Local bot instance")
        Container(config_local, "Configuration Files", "JSON/YAML", "Trading parameters")
    }

    Deployment_Node(vps, "VPS/Cloud Server", "Ubuntu 22.04") {
        Container(bot_prod, "Passivbot Service", "Python + SystemD", "Production bot instance")
        Container(web_prod, "Web Dashboard", "FastAPI + Nginx", "Monitoring interface")
        Container(db_prod, "Database", "PostgreSQL", "Trading data storage")
        Container(logs, "Log Files", "Structured Logs", "System monitoring")
    }

    Deployment_Node(exchanges_cloud, "Exchange APIs", "Cloud Infrastructure") {
        Container(binance_api, "Binance API", "REST/WebSocket", "Trading operations")
        Container(bybit_api, "Bybit API", "REST/WebSocket", "Trading operations")
    }

    Deployment_Node(notification_services, "Notification Services", "External APIs") {
        Container(telegram_api, "Telegram Bot API", "HTTPS", "Alert notifications")
        Container(discord_webhook, "Discord Webhook", "HTTPS", "Alert notifications")
    }

    Rel(cli_local, config_local, "Reads", "File I/O")
    Rel(bot_prod, db_prod, "Stores data", "PostgreSQL protocol")
    Rel(web_prod, bot_prod, "API calls", "HTTP/JSON")
    Rel(bot_prod, logs, "Writes", "File I/O")
    
    Rel(cli_local, binance_api, "Trading", "HTTPS/WSS")
    Rel(bot_prod, binance_api, "Trading", "HTTPS/WSS")
    Rel(cli_local, bybit_api, "Trading", "HTTPS/WSS")
    Rel(bot_prod, bybit_api, "Trading", "HTTPS/WSS")
    
    Rel(bot_prod, telegram_api, "Notifications", "HTTPS")
    Rel(bot_prod, discord_webhook, "Notifications", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Data Flow Diagram

Shows how data flows through the system during trading operations.

```mermaid
flowchart TB
    subgraph "External Data Sources"
        Exchange[Exchange APIs<br/>Market Data & Orders]
        Config[Configuration Files<br/>Strategy Parameters]
    end

    subgraph "Data Ingestion"
        WebSocket[WebSocket Handler<br/>Real-time Data]
        REST[REST API Handler<br/>Account Data]
        ConfigLoader[Config Loader<br/>Pydantic Validation]
    end

    subgraph "Core Processing"
        MarketData[Market Data Processor<br/>Price, Volume, Orderbook]
        AccountData[Account Data Manager<br/>Balances, Positions]
        RiskEngine[Risk Engine<br/>Validation & Limits]
        StrategyEngine[Strategy Engine<br/>Trading Logic]
    end

    subgraph "Decision Making"
        GridLogic[Grid Strategy Logic<br/>Level Calculation]
        DCALogic[DCA Strategy Logic<br/>Safety Orders]
        OrderLogic[Order Decision Engine<br/>Buy/Sell Signals]
    end

    subgraph "Order Execution"
        OrderManager[Order Manager<br/>Placement & Tracking]
        ExchangeAPI[Exchange API Client<br/>Order Submission]
    end

    subgraph "Data Persistence"
        Database[(Database<br/>Trading History)]
        Logs[Log Files<br/>Audit Trail]
    end

    subgraph "Monitoring & Alerts"
        WebDash[Web Dashboard<br/>Real-time Monitoring]
        Notifications[Notification Service<br/>Alerts & Updates]
    end

    Exchange --> WebSocket
    Exchange --> REST
    Config --> ConfigLoader

    WebSocket --> MarketData
    REST --> AccountData
    ConfigLoader --> StrategyEngine

    MarketData --> RiskEngine
    AccountData --> RiskEngine
    RiskEngine --> StrategyEngine

    StrategyEngine --> GridLogic
    StrategyEngine --> DCALogic
    GridLogic --> OrderLogic
    DCALogic --> OrderLogic

    OrderLogic --> OrderManager
    OrderManager --> ExchangeAPI
    ExchangeAPI --> Exchange

    OrderManager --> Database
    MarketData --> Database
    AccountData --> Database
    StrategyEngine --> Logs

    Database --> WebDash
    OrderManager --> WebDash
    RiskEngine --> Notifications
    OrderManager --> Notifications

    style Exchange fill:#e1f5fe
    style Database fill:#f3e5f5
    style RiskEngine fill:#ffebee
    style StrategyEngine fill:#e8f5e8
```

## Security Architecture

Shows security boundaries and data protection measures.

```mermaid
C4Container
    title Security Architecture - Passivbot v2.0

    Person(trader, "Trader", "System operator")

    System_Boundary(secure_zone, "Secure Zone - Private Network") {
        Container(cli, "CLI Interface", "Local Access", "Direct system access with full permissions")
        
        Container_Boundary(app_layer, "Application Layer") {
            Container(bot, "Trading Bot", "Python Process", "Core trading logic with API credentials")
            Container(web, "Web Dashboard", "FastAPI + Auth", "Monitoring interface with JWT authentication")
        }
        
        Container_Boundary(data_layer, "Data Layer") {
            Container(db, "Database", "Encrypted Storage", "Trading data with encryption at rest")
            Container(config, "Configuration", "Encrypted Files", "API keys and sensitive parameters")
            Container(logs, "Audit Logs", "Secured Files", "System activity tracking")
        }
    }

    System_Boundary(dmz, "DMZ - Public Access") {
        Container(reverse_proxy, "Reverse Proxy", "Nginx + SSL", "TLS termination and rate limiting")
    }

    System_Ext(exchanges, "Exchange APIs", "External endpoints with API authentication")
    System_Ext(notifications, "Notification Services", "External APIs with token authentication")

    Rel(trader, cli, "Direct access", "Local shell")
    Rel(trader, reverse_proxy, "HTTPS", "Web browser")
    Rel(reverse_proxy, web, "HTTP", "Internal network")
    
    Rel(cli, bot, "Control commands", "Process signals")
    Rel(web, bot, "Status queries", "Internal API")
    
    Rel(bot, db, "Encrypted queries", "TLS connection")
    Rel(bot, config, "Read secrets", "File encryption")
    Rel(bot, logs, "Audit events", "Secured writes")
    
    Rel(bot, exchanges, "Authenticated API", "HTTPS + Signatures")
    Rel(bot, notifications, "Token auth", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="2")
```

## Key Architecture Principles

### 1. **Separation of Concerns**
- **Exchange Layer**: Handles all external API interactions
- **Strategy Layer**: Contains pure trading logic
- **Risk Layer**: Manages safety and compliance
- **Data Layer**: Handles persistence and state management

### 2. **Scalability**
- **Async Architecture**: Non-blocking I/O for concurrent operations
- **Modular Design**: Easy to add new exchanges and strategies
- **Resource Management**: Rate limiting and connection pooling

### 3. **Reliability**
- **Error Handling**: Comprehensive exception hierarchy
- **State Recovery**: Persistent state across restarts
- **Circuit Breakers**: Automatic failure detection and recovery

### 4. **Security**
- **Credential Management**: Encrypted storage of API keys
- **Input Validation**: Pydantic models for all data
- **Audit Logging**: Complete activity tracking
- **Network Security**: TLS encryption for all communications

### 5. **Observability**
- **Structured Logging**: JSON logs for analysis
- **Metrics Collection**: Performance and trading metrics
- **Real-time Monitoring**: Web dashboard with live updates
- **Alerting**: Multi-channel notification system

This C4 model provides a comprehensive view of the Passivbot architecture from high-level system context down to detailed component interactions, making it easy to understand the system at different levels of abstraction.
