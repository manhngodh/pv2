# Quick Reference - Trading Logic Flow

## Grid Trading Strategy - Simplified

```
1. Initialize Grid
   ├── Get current market price
   ├── Calculate grid levels (above & below price)
   ├── Place buy orders below current price
   └── Place sell orders above current price

2. Monitor Orders
   ├── Check for filled orders every second
   ├── When buy order fills → place sell order above
   ├── When sell order fills → place buy order below
   └── Maintain grid coverage

3. Rebalance Check
   ├── If price moves too far from grid center
   ├── Cancel all existing orders
   ├── Recalculate grid around new price
   └── Place new orders
```

## DCA Strategy - Simplified

```
1. Place Base Order
   ├── Market buy with base order size
   ├── Set entry price
   └── Place take profit order

2. Monitor Price Action
   ├── If price drops X% → place safety order
   ├── If safety order fills → update average entry
   ├── Update take profit based on new average
   └── Repeat until max safety orders reached

3. Exit Conditions
   ├── Take profit fills → restart cycle
   ├── Stop loss triggered → sell all & restart
   └── Max safety orders → wait for recovery
```

## Risk Management - Key Checks

```
1. Emergency Stop Check
   └── If activated → cancel all orders & stop

2. Drawdown Check
   ├── Calculate: (Peak - Current) / Peak * 100
   └── If > max → stop trading & alert

3. Position Size Check
   ├── For each position: check if > max size
   └── If exceeded → reduce position

4. Total Exposure Check
   ├── Sum all position values
   └── If > max → reduce largest positions

5. Order Count Check
   ├── Count orders per symbol
   └── If > max → cancel oldest orders
```

## Main Bot Loop - Every Second

```
┌─ Update Account Data
│  ├── Get latest balances
│  ├── Get current positions  
│  └── Update open orders
│
├─ Risk Management Check
│  ├── Check emergency stop
│  ├── Check drawdown limits
│  ├── Check position sizes
│  └── Check exposure limits
│
├─ Execute Strategies
│  ├── For each enabled strategy
│  ├── Update market data
│  ├── Execute strategy logic
│  └── Place/cancel orders as needed
│
└─ Sleep 1 second → repeat
```

## Configuration Flow

```
1. Load config.json
   ├── Validate structure
   ├── Check required fields
   └── Warn about risks

2. Initialize Exchange
   ├── Create exchange instance
   ├── Test API connection
   └── Setup rate limiting

3. Initialize Strategies
   ├── Create strategy instances
   ├── Validate configurations
   └── Setup initial state

4. Start Trading Loop
   └── Begin main execution cycle
```

## Error Handling Strategy

```
Exchange Errors:
├── Connection Error → Retry with backoff
├── API Rate Limit → Wait & retry
├── Insufficient Balance → Log & skip order
└── Authentication → Stop & alert

Strategy Errors:
├── Invalid Config → Stop strategy
├── Execution Error → Log & continue
└── Risk Violation → Emergency stop

System Errors:
├── Database Error → Retry operation
├── Network Error → Reconnect
└── Critical Error → Graceful shutdown
```
