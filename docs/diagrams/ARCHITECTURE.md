# Passivbot v2.0 Architecture Diagrams

This document contains various diagrams to visualize the system architecture, data flow, and trading logic.

## 1. System Architecture Overview

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

## 2. Bot Lifecycle Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Bot
    participant Exchange
    participant Strategy
    participant Risk
    
    User->>CLI: passivbot run config.json
    CLI->>Bot: create_bot(config)
    
    Bot->>Bot: _setup_logging()
    Bot->>Exchange: connect()
    Exchange-->>Bot: connection_established
    
    Bot->>Strategy: initialize_strategies()
    Strategy-->>Bot: strategies_ready
    
    loop Main Trading Loop
        Bot->>Bot: _update_account_data()
        Bot->>Risk: _check_risk_management()
        
        alt Risk Check Passes
            Bot->>Strategy: execute()
            Strategy->>Exchange: place_orders()
            Exchange-->>Strategy: order_responses
            Strategy-->>Bot: execution_complete
        else Risk Check Fails
            Risk-->>Bot: risk_violation
            Bot->>Bot: emergency_stop()
        end
        
        Bot->>Bot: sleep(1s)
    end
    
    User->>CLI: Ctrl+C
    CLI->>Bot: stop()
    Bot->>Strategy: cleanup()
    Bot->>Exchange: disconnect()
```

## 3. Configuration System Structure

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

## 4. Exchange Layer Architecture

```mermaid
graph TB
    subgraph "Exchange Layer"
        Base[BaseExchange<br/>Abstract Interface]
        
        subgraph "Implementations"
            Binance[BinanceExchange]
            Bybit[BybitExchange] 
            OKX[OKXExchange<br/>Future]
        end
        
        Registry[Exchange Registry<br/>get_exchange()]
    end
    
    subgraph "Core Methods"
        Account[Account Methods<br/>get_balances()<br/>get_positions()]
        Orders[Order Methods<br/>place_order()<br/>cancel_order()<br/>get_orders()]
        Market[Market Data<br/>get_market_data()<br/>get_orderbook()]
        Trading[Trading Helpers<br/>buy_market()<br/>sell_limit()<br/>etc.]
    end
    
    subgraph "External APIs"
        BinanceAPI[Binance API<br/>REST + WebSocket]
        BybitAPI[Bybit API<br/>REST + WebSocket]
        OKXAPI[OKX API<br/>REST + WebSocket]
    end
    
    Base --> Binance
    Base --> Bybit
    Base --> OKX
    
    Registry --> Base
    
    Base --> Account
    Base --> Orders
    Base --> Market
    Base --> Trading
    
    Binance --> BinanceAPI
    Bybit --> BybitAPI
    OKX --> OKXAPI
    
    style Base fill:#e3f2fd
    style Registry fill:#f3e5f5
```

## 5. Grid Trading Strategy Logic

```mermaid
flowchart TD
    Start[Grid Strategy Start] --> Init{Initialized?}
    
    Init -->|No| GetPrice[Get Current Price]
    GetPrice --> CalcLevels[Calculate Grid Levels]
    CalcLevels --> PlaceOrders[Place Initial Orders]
    PlaceOrders --> SetInit[Set Initialized = True]
    
    Init -->|Yes| Update[Update Market Data & Orders]
    SetInit --> Update
    
    Update --> CheckFills[Check for Filled Orders]
    
    CheckFills --> HasFills{Orders Filled?}
    
    HasFills -->|Yes| ProcessFill[Process Filled Orders]
    ProcessFill --> PlaceOpposite[Place Opposite Orders]
    PlaceOpposite --> CheckRebalance
    
    HasFills -->|No| CheckRebalance[Check Rebalancing Need]
    
    CheckRebalance --> NeedRebalance{Price Deviation > Threshold?}
    
    NeedRebalance -->|Yes| CancelAll[Cancel All Orders]
    CancelAll --> ResetGrid[Reset Grid Levels]
    ResetGrid --> CalcLevels
    
    NeedRebalance -->|No| EnsureCoverage[Ensure Grid Coverage]
    EnsureCoverage --> Wait[Wait for Next Cycle]
    Wait --> Update
    
    subgraph "Grid Level Calculation"
        CalcLevels --> GetSpacing[Get Price Spacing %]
        GetSpacing --> CalcUp[Calculate Levels Above Price]
        CalcUp --> CalcDown[Calculate Levels Below Price]
        CalcDown --> ValidateBounds[Validate Boundaries]
    end
    
    subgraph "Order Placement Logic"
        PlaceOrders --> CalcQty[Calculate Quantity per Level]
        CalcQty --> BuyBelow[Place Buy Orders Below Price]
        BuyBelow --> SellAbove[Place Sell Orders Above Price]
    end
    
    style Start fill:#e8f5e8
    style ProcessFill fill:#fff3e0
    style CancelAll fill:#ffebee
```

## 6. DCA Strategy Logic

```mermaid
flowchart TD
    Start[DCA Strategy Start] --> Init{Initialized?}
    
    Init -->|No| CheckBalance[Check USDT Balance]
    CheckBalance --> PlaceBase[Place Base Order<br/>Market Buy]
    PlaceBase --> SetEntry[Set Entry Price]
    SetEntry --> PlaceTP[Place Take Profit Order]
    PlaceTP --> SetInit[Set Initialized = True]
    
    Init -->|Yes| Update[Update Orders & Positions]
    SetInit --> Update
    
    Update --> CheckBase{Base Order Filled?}
    
    CheckBase -->|Yes| UpdateEntry[Update Entry Price]
    UpdateEntry --> UpdateTP[Update Take Profit]
    UpdateTP --> CheckSafety
    
    CheckBase -->|No| CheckSafety[Check Safety Orders]
    
    CheckSafety --> SafetyFilled{Safety Order Filled?}
    
    SafetyFilled -->|Yes| IncSafetyCount[Increment Safety Count]
    IncSafetyCount --> RecalcEntry[Recalculate Avg Entry]
    RecalcEntry --> UpdateTP
    
    SafetyFilled -->|No| CheckTP[Check Take Profit]
    
    CheckTP --> TPFilled{Take Profit Filled?}
    
    TPFilled -->|Yes| Reset[Reset DCA State]
    Reset --> Profit[Profit Realized]
    Profit --> Start
    
    TPFilled -->|No| CheckPrice[Check Current Price]
    
    CheckPrice --> NeedSafety{Price Hit Safety Level?}
    
    NeedSafety -->|Yes| CheckCount{Safety Count < Max?}
    CheckCount -->|Yes| PlaceSafety[Place Safety Order]
    PlaceSafety --> Wait
    CheckCount -->|No| Wait
    
    NeedSafety -->|No| CheckStopLoss{Stop Loss Enabled?}
    
    CheckStopLoss -->|Yes| StopLossHit{Price Hit Stop Loss?}
    StopLossHit -->|Yes| ExecuteStop[Execute Stop Loss<br/>Market Sell All]
    ExecuteStop --> Reset
    
    CheckStopLoss -->|No| Wait[Wait for Next Cycle]
    StopLossHit -->|No| Wait
    Wait --> Update
    
    subgraph "Safety Order Calculation"
        PlaceSafety --> CalcPrice[Price = Entry × (1 - deviation × step_scale^count)]
        CalcPrice --> CalcQty[Quantity = safety_size × volume_scale^count / price]
    end
    
    subgraph "Take Profit Calculation"
        PlaceTP --> TPPrice[TP Price = Entry × (1 + tp_percentage)]
        TPPrice --> TPQty[TP Quantity = Total Position Size]
    end
    
    style Start fill:#e8f5e8
    style Profit fill:#e8f5e8
    style ExecuteStop fill:#ffebee
    style PlaceSafety fill:#fff3e0
```

## 7. Risk Management Flow

```mermaid
flowchart TD
    Start[Risk Check Start] --> EmergencyStop{Emergency Stop<br/>Activated?}
    
    EmergencyStop -->|Yes| StopAll[Stop All Trading<br/>Cancel Orders]
    StopAll --> Alert[Send Alert]
    Alert --> End[End Trading]
    
    EmergencyStop -->|No| CheckDrawdown[Calculate Current Drawdown]
    
    CheckDrawdown --> DrawdownCalc[Drawdown = (Peak - Current) / Peak × 100]
    
    DrawdownCalc --> DrawdownCheck{Drawdown > Max?}
    
    DrawdownCheck -->|Yes| DrawdownStop[Maximum Drawdown<br/>Exceeded]
    DrawdownStop --> StopAll
    
    DrawdownCheck -->|No| CheckPosition[Check Position Sizes]
    
    CheckPosition --> PositionLoop{For Each Position}
    
    PositionLoop --> CheckSize{Position > Max Size?}
    
    CheckSize -->|Yes| ReducePosition[Reduce Position<br/>Partial Close]
    ReducePosition --> LogWarning[Log Warning]
    LogWarning --> NextPosition
    
    CheckSize -->|No| NextPosition[Next Position]
    NextPosition --> MorePositions{More Positions?}
    
    MorePositions -->|Yes| PositionLoop
    MorePositions -->|No| CheckExposure[Check Total Exposure]
    
    CheckExposure --> ExposureCalc[Total Exposure = Sum(Position Values)]
    ExposureCalc --> ExposureCheck{Exposure > Max?}
    
    ExposureCheck -->|Yes| ReduceExposure[Reduce Largest Positions]
    ReduceExposure --> LogWarning
    
    ExposureCheck -->|No| CheckOrders[Check Order Counts]
    
    CheckOrders --> OrderLoop{For Each Symbol}
    OrderLoop --> CountOrders[Count Open Orders]
    CountOrders --> OrderCheck{Orders > Max per Symbol?}
    
    OrderCheck -->|Yes| CancelOldest[Cancel Oldest Orders]
    CancelOldest --> NextSymbol
    
    OrderCheck -->|No| NextSymbol[Next Symbol]
    NextSymbol --> MoreSymbols{More Symbols?}
    
    MoreSymbols -->|Yes| OrderLoop
    MoreSymbols -->|No| Pass[Risk Check Passed]
    
    Pass --> Continue[Continue Trading]
    
    style Start fill:#e3f2fd
    style Pass fill:#e8f5e8
    style StopAll fill:#ffebee
    style DrawdownStop fill:#ffebee
    style ReducePosition fill:#fff3e0
```

## 8. Data Models Relationship

```mermaid
erDiagram
    Order {
        string id PK
        string client_id
        string symbol
        enum side
        enum type
        decimal quantity
        decimal price
        enum status
        decimal filled_quantity
        decimal average_price
        datetime timestamp
        datetime updated_at
    }
    
    Position {
        string symbol PK
        enum side
        decimal size
        decimal entry_price
        decimal mark_price
        decimal unrealized_pnl
        decimal realized_pnl
        datetime timestamp
    }
    
    Balance {
        string asset PK
        decimal free
        decimal locked
        datetime timestamp
    }
    
    Trade {
        string id PK
        string order_id FK
        string symbol
        enum side
        decimal quantity
        decimal price
        decimal fee
        string fee_asset
        datetime timestamp
    }
    
    MarketData {
        string symbol PK
        decimal price
        decimal bid
        decimal ask
        decimal volume_24h
        decimal change_24h
        datetime timestamp
    }
    
    Strategy {
        string id PK
        string symbol
        enum type
        json config
        bool enabled
        datetime created_at
        datetime updated_at
    }
    
    Order ||--|| Trade : "generates"
    Position ||--o{ Order : "affects"
    Strategy ||--o{ Order : "creates"
    Strategy ||--|| Position : "manages"
    Balance ||--o{ Order : "constrains"
```

## 9. WebSocket Data Flow

```mermaid
sequenceDiagram
    participant Bot
    participant Exchange
    participant WebSocket
    participant Strategy
    participant DB
    
    Bot->>Exchange: connect_websocket()
    Exchange->>WebSocket: establish_connection()
    WebSocket-->>Exchange: connection_ready
    
    loop Real-time Data Stream
        WebSocket->>Exchange: market_data_update
        Exchange->>Exchange: parse_message()
        
        alt Order Update
            Exchange->>Bot: order_update_event
            Bot->>Strategy: handle_order_update()
            Strategy->>DB: update_order_status()
        else Price Update
            Exchange->>Bot: price_update_event
            Bot->>Strategy: handle_price_update()
            Strategy->>Strategy: check_triggers()
        else Balance Update
            Exchange->>Bot: balance_update_event
            Bot->>Bot: update_account_state()
        end
    end
    
    Note over Bot,DB: Real-time updates enable<br/>immediate strategy reactions
```

## 10. Error Handling Hierarchy

```mermaid
graph TD
    BaseError[PassivbotError<br/>Base Exception] --> ConfigError[ConfigurationError]
    BaseError --> ExchangeError[ExchangeError]
    BaseError --> StrategyError[StrategyError]
    BaseError --> RiskError[RiskManagementError]
    BaseError --> DataError[DataError]
    BaseError --> ValidationError[ValidationError]
    BaseError --> BacktestError[BacktestError]
    BaseError --> NotificationError[NotificationError]
    BaseError --> WebError[WebInterfaceError]
    
    ExchangeError --> ConnError[ExchangeConnectionError]
    ExchangeError --> APIError[ExchangeAPIError]
    ExchangeError --> BalanceError[InsufficientBalanceError]
    
    StrategyError --> InvalidStrategy[InvalidStrategyError]
    StrategyError --> ExecutionError[StrategyExecutionError]
    
    RiskError --> MaxPositionError[MaxPositionSizeExceededError]
    RiskError --> DrawdownError[MaxDrawdownExceededError]
    
    DataError --> DBError[DatabaseError]
    
    ValidationError --> PriceError[InvalidPriceError]
    ValidationError --> QtyError[InvalidQuantityError]
    
    BacktestError --> DataInsufficient[InsufficientDataError]
    
    subgraph "Error Handling Utils"
        HandleExchange[handle_exchange_error()]
        IsRetriable[is_retriable_error()]
        RetryLogic[Exponential Backoff<br/>Circuit Breaker]
    end
    
    ExchangeError -.-> HandleExchange
    APIError -.-> IsRetriable
    ConnError -.-> RetryLogic
    
    style BaseError fill:#e3f2fd
    style ExchangeError fill:#fff3e0
    style StrategyError fill:#e8f5e8
    style RiskError fill:#ffebee
```

These diagrams provide a comprehensive visualization of:

1. **System Architecture** - Overall component structure
2. **Bot Lifecycle** - Sequence of operations during bot execution
3. **Configuration** - Data model relationships
4. **Exchange Layer** - Abstraction and implementation structure  
5. **Grid Strategy** - Trading logic flow
6. **DCA Strategy** - Dollar cost averaging logic
7. **Risk Management** - Safety checks and controls
8. **Data Models** - Entity relationships
9. **WebSocket Flow** - Real-time data handling
10. **Error Handling** - Exception hierarchy and recovery

These visual representations help understand the complex interactions between different parts of the system and the flow of data and control throughout the trading bot.
