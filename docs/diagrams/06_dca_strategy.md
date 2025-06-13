# DCA (Dollar Cost Averaging) Strategy Logic

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

## DCA Strategy Algorithm

### Core Concept
Dollar Cost Averaging (DCA) is a strategy that buys into a position gradually as the price falls, reducing the average entry price. When the price recovers above the average entry price plus profit margin, the entire position is sold for a profit.

### Algorithm Components

#### 1. Base Order
- **Initial Purchase**: Market buy order with base order size
- **Entry Price**: Records the initial entry price
- **Take Profit**: Places sell order at entry price + profit percentage

#### 2. Safety Orders
- **Trigger Condition**: Price drops below entry by deviation percentage
- **Progressive Sizing**: Each safety order can be larger than the previous
- **Price Scaling**: Safety order prices scale with step multiplier
- **Volume Scaling**: Safety order sizes scale with volume multiplier

#### 3. Take Profit Management
- **Dynamic Updates**: Recalculated after each safety order fill
- **Average Entry**: Based on weighted average of all filled orders
- **Profit Target**: Fixed percentage above average entry price

#### 4. Stop Loss (Optional)
- **Risk Protection**: Limits maximum loss per DCA cycle
- **Market Exit**: Sells entire position at market price
- **Cycle Reset**: Starts new DCA cycle after stop loss

### Configuration Parameters

#### Order Sizing
- **`base_order_size`**: Size of initial market buy (e.g., $100)
- **`safety_order_size`**: Base size for safety orders (e.g., $50)
- **`max_safety_orders`**: Maximum number of safety orders (e.g., 5)

#### Price Levels
- **`price_deviation_percentage`**: Price drop to trigger safety order (e.g., 2%)
- **`safety_order_step_scale`**: Price step multiplier (e.g., 1.2)
- **`take_profit_percentage`**: Profit target percentage (e.g., 1.5%)

#### Risk Management
- **`safety_order_volume_scale`**: Volume scaling factor (e.g., 1.5)
- **`stop_loss_percentage`**: Maximum loss threshold (optional)

### Mathematical Formulas

#### Safety Order Price Calculation
```
safety_price = entry_price × (1 - deviation_pct × step_scale^order_count)
```

#### Safety Order Quantity Calculation
```
safety_quantity = (safety_size × volume_scale^order_count) / safety_price
```

#### Average Entry Price Update
```
new_avg = (total_cost + new_order_cost) / (total_quantity + new_quantity)
```

#### Take Profit Price
```
take_profit_price = average_entry_price × (1 + profit_percentage)
```

### Example DCA Cycle

#### Initial Setup
- **Symbol**: BTCUSDT
- **Base Order**: $100 at $50,000 = 0.002 BTC
- **Safety Orders**: $50 each, max 3 orders
- **Price Deviation**: 3% per safety order
- **Take Profit**: 2% above average entry

#### Price Movement Scenario
1. **Base Order**: Buy 0.002 BTC at $50,000
2. **Price Drops to $48,500** (-3%): Safety Order 1 - Buy $50 worth
3. **Price Drops to $47,090** (-3% from previous): Safety Order 2 - Buy $75 worth
4. **Price Recovers to $49,000**: Take profit order fills, cycle complete

#### Profit Calculation
- **Total Cost**: $100 + $50 + $75 = $225
- **Average Entry**: ~$48,000
- **Take Profit**: $48,000 × 1.02 = $48,960
- **Profit**: Position sold above average entry + 2%

### Risk Management Features

#### Position Limits
- **Maximum Position**: Limits total DCA position size
- **Balance Requirements**: Ensures sufficient funds for all safety orders
- **Exposure Control**: Manages total exposure across all DCA positions

#### Safety Mechanisms
- **Safety Order Limits**: Prevents unlimited averaging down
- **Stop Loss Protection**: Optional maximum loss protection
- **Market Condition Checks**: Pause during extreme volatility

### Implementation State Management

#### Order Tracking
```python
self._base_order: Optional[Order]         # Initial market buy
self._safety_orders: List[Order]          # Progressive safety orders
self._take_profit_order: Optional[Order]  # Exit order
self._entry_price: Optional[Decimal]      # Weighted average entry
self._safety_order_count: int             # Number of safety orders used
```

#### State Transitions
1. **Uninitialized** → Place base order
2. **Base Filled** → Place take profit, monitor for safety triggers
3. **Safety Triggered** → Place safety order, update averages
4. **Take Profit Filled** → Reset state, start new cycle
5. **Stop Loss Hit** → Emergency exit, reset state

### Performance Characteristics

#### Best Market Conditions
- **Volatile but Recoverable**: Markets with dips followed by recovery
- **Bull Market Corrections**: Temporary pullbacks in uptrending markets
- **Range-Bound Markets**: Oscillating within predictable ranges

#### Risk Scenarios
- **Sustained Bear Markets**: Continuous price decline without recovery
- **Flash Crashes**: Rapid price drops that trigger all safety orders
- **Low Liquidity**: Difficulty executing orders at target prices

### Advanced Features

#### Dynamic Adjustments
- **Volatility-Based Scaling**: Adjust deviation based on market volatility
- **Time-Based Adjustments**: Modify parameters based on market sessions
- **Correlation Analysis**: Consider correlation with other assets

#### Multi-Asset DCA
- **Portfolio DCA**: Run DCA on multiple uncorrelated assets
- **Risk Distribution**: Spread DCA risk across different markets
- **Rebalancing**: Periodic rebalancing of DCA allocations
