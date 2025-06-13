# Bot Lifecycle Flow

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

## Lifecycle Phases

### 1. Initialization Phase
1. **Configuration Loading**: Parse and validate configuration file
2. **Logging Setup**: Configure logging levels and output destinations
3. **Exchange Connection**: Establish API connections and test connectivity
4. **Strategy Initialization**: Create and configure trading strategies

### 2. Main Trading Loop
1. **Account Data Update**: Refresh balances, positions, and orders
2. **Risk Management Check**: Validate all risk parameters
3. **Strategy Execution**: Execute active trading strategies
4. **Order Management**: Place, modify, or cancel orders as needed
5. **Sleep Cycle**: Wait 1 second before next iteration

### 3. Shutdown Phase
1. **Signal Handling**: Respond to interrupt signals (Ctrl+C)
2. **Strategy Cleanup**: Cancel open orders and cleanup resources
3. **Exchange Disconnect**: Close API connections gracefully
4. **Final Logging**: Log shutdown completion and statistics
