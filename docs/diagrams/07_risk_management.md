# Risk Management Flow

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

## Risk Management System

### Core Philosophy
Risk management is the first priority in the Passivbot system. All trading decisions must pass through risk checks before execution. The system implements multiple layers of protection to prevent catastrophic losses.

### Risk Check Hierarchy

#### 1. Emergency Stop Check
- **Immediate Halt**: Manual emergency stop activation
- **System-Wide**: Affects all strategies and symbols
- **Order Cancellation**: Cancels all open orders immediately
- **Alert System**: Sends notifications to all configured channels

#### 2. Drawdown Protection
- **Peak Tracking**: Monitors portfolio high-water mark
- **Real-Time Calculation**: Continuous drawdown monitoring
- **Automatic Shutdown**: Stops trading when limit exceeded
- **Configurable Threshold**: User-defined maximum drawdown percentage

#### 3. Position Size Limits
- **Per-Symbol Limits**: Maximum position size per trading pair
- **Position Reduction**: Automatic partial position closing
- **Warning System**: Logs violations for monitoring
- **Gradual Adjustment**: Reduces positions incrementally

#### 4. Total Exposure Control
- **Portfolio-Wide**: Monitors total exposure across all positions
- **Dynamic Calculation**: Real-time exposure computation
- **Largest First**: Reduces largest positions when over limit
- **Proportional Reduction**: Maintains relative position sizes

#### 5. Order Management
- **Order Counting**: Tracks orders per symbol
- **Oldest First**: Cancels oldest orders when limit exceeded
- **Strategy Coordination**: Ensures strategies stay within limits
- **Resource Protection**: Prevents exchange rate limiting

### Risk Configuration Parameters

#### Drawdown Settings
```python
max_drawdown_percentage: Decimal = 20.0  # Maximum portfolio drawdown
stop_loss_percentage: Optional[Decimal]  # Global stop loss
emergency_stop: bool = False             # Manual emergency stop
```

#### Position Limits
```python
max_position_size: Decimal = 1000.0      # Maximum position size
max_total_exposure: Decimal = 10000.0    # Maximum total exposure
max_orders_per_symbol: int = 10          # Maximum orders per symbol
```

### Drawdown Calculation

#### Formula
```
Current Drawdown = (Peak Portfolio Value - Current Portfolio Value) / Peak Portfolio Value × 100
```

#### Implementation
```python
async def _calculate_drawdown(self) -> Decimal:
    current_value = await self._get_portfolio_value()
    if current_value > self._peak_value:
        self._peak_value = current_value
    
    if self._peak_value > 0:
        drawdown = (self._peak_value - current_value) / self._peak_value * 100
        return drawdown
    return Decimal("0")
```

### Position Size Management

#### Size Calculation
```python
def calculate_position_value(position: Position, current_price: Decimal) -> Decimal:
    return position.size * current_price
```

#### Reduction Strategy
1. **Identify Oversized**: Find positions exceeding limits
2. **Calculate Reduction**: Determine amount to reduce
3. **Partial Close**: Execute market orders to reduce size
4. **Monitor Impact**: Track reduction effectiveness

### Exposure Management

#### Total Exposure Calculation
```python
total_exposure = sum(
    abs(position.size * current_price) 
    for position in all_positions
)
```

#### Reduction Priority
1. **Largest Positions**: Target biggest exposures first
2. **Risk-Adjusted**: Consider position volatility
3. **Strategy Impact**: Minimize strategy disruption
4. **Market Conditions**: Consider liquidity and timing

### Alert and Notification System

#### Alert Levels
- **INFO**: Normal operation status
- **WARNING**: Risk limit approached
- **ERROR**: Risk limit exceeded
- **CRITICAL**: Emergency stop activated

#### Notification Channels
- **Logging**: Detailed logs for all risk events
- **Telegram**: Real-time mobile notifications
- **Discord**: Team communication channels
- **Email**: Detailed risk reports

### Risk Metrics and Monitoring

#### Key Performance Indicators
- **Current Drawdown**: Real-time drawdown percentage
- **Peak Portfolio Value**: Historical maximum value
- **Position Count**: Number of open positions
- **Order Count**: Number of pending orders
- **Exposure Ratio**: Current vs. maximum exposure

#### Historical Tracking
- **Drawdown History**: Track drawdown over time
- **Risk Violations**: Log all risk limit breaches
- **Performance Impact**: Measure risk management effectiveness
- **Recovery Analysis**: Monitor recovery after risk events

### Integration with Trading Strategies

#### Pre-Trade Checks
```python
async def validate_trade(self, order: Order) -> bool:
    # Check if trade would exceed position limits
    # Check if trade would exceed exposure limits
    # Check emergency stop status
    # Validate against current drawdown
    return risk_check_passed
```

#### Post-Trade Monitoring
```python
async def monitor_position(self, position: Position) -> None:
    # Update portfolio value
    # Recalculate drawdown
    # Check position size limits
    # Update exposure calculations
```

### Emergency Response Procedures

#### Automatic Responses
1. **Order Cancellation**: Cancel all pending orders
2. **Position Alerts**: Notify about large positions
3. **Strategy Pause**: Temporarily disable strategies
4. **System Monitoring**: Increase monitoring frequency

#### Manual Interventions
1. **Emergency Stop**: Complete trading halt
2. **Position Closure**: Manual position liquidation
3. **Configuration Update**: Adjust risk parameters
4. **System Restart**: Restart with updated settings

### Risk Optimization

#### Dynamic Risk Adjustment
- **Volatility-Based**: Adjust limits based on market volatility
- **Performance-Based**: Modify based on strategy performance
- **Time-Based**: Different limits for different market sessions
- **Correlation-Based**: Account for asset correlations

#### Backtesting Risk Models
- **Historical Simulation**: Test risk models on historical data
- **Scenario Analysis**: Test extreme market scenarios
- **Stress Testing**: Validate under market stress conditions
- **Performance Attribution**: Analyze risk vs. return trade-offs
