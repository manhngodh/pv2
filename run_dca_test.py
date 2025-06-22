import asyncio
import logging
import signal
import sys
import pandas as pd
from decimal import Decimal
from datetime import datetime

from passivbot.core.config import StrategyConfig, DCAConfig
from passivbot.core.types import StrategyType
from passivbot.exchanges.simulator import SimulatorExchange
from passivbot.strategies.dca import DCAStrategy

# Configure logging to see the output from the simulator and strategy
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add signal handler for graceful shutdown
def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class HistoricalDataSimulator(SimulatorExchange):
    """Enhanced simulator that uses historical CSV data for backtesting."""
    
    def __init__(self, csv_file: str, **kwargs):
        super().__init__(**kwargs)
        self.csv_file = csv_file
        self.historical_data = self._load_historical_data()
        self.current_index = 0
        self.max_index = len(self.historical_data) - 1
        print(f"📊 Loaded {len(self.historical_data)} historical data points from {csv_file}")
        
    def _load_historical_data(self) -> pd.DataFrame:
        """Load historical data from CSV file."""
        df = pd.read_csv(self.csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    
    async def fetch_ticker(self, symbol: str):
        """Override to use historical data instead of live data."""
        if self.current_index >= self.max_index:
            print("🏁 Reached end of historical data")
            # Return last known price
            row = self.historical_data.iloc[self.max_index]
        else:
            row = self.historical_data.iloc[self.current_index]
            self.current_index += 1
            
        price = Decimal(str(row['close']))
        self._last_price = price
        
        # Show progress through historical data
        if self.current_index % 25 == 0:
            print(f"📈 Historical data progress: {self.current_index}/{self.max_index} ({row['timestamp']})")
        
        from passivbot.core.types import Ticker
        return Ticker(
            symbol=symbol,
            price=price,
            bid=Decimal(str(row['low'])),
            ask=Decimal(str(row['high'])),
            volume=Decimal(str(row['volume']))
        )
    
    def get_current_timestamp(self):
        """Get current timestamp from historical data."""
        if self.current_index < len(self.historical_data):
            return self.historical_data.iloc[self.current_index]['timestamp']
        return self.historical_data.iloc[-1]['timestamp']

async def main():
    """
    Main function to set up and run the DCA strategy backtest with historical data.
    """
    print("🚀 Starting DCA Strategy Backtest")
    
    # 1. Define the DCA Strategy Configuration
    dca_config = DCAConfig(
        base_order_size=Decimal("100"),        # $100 initial buy
        safety_order_size=Decimal("50"),       # $50 safety orders
        max_safety_orders=5,                   # Maximum 5 safety orders
        price_deviation_percentage=Decimal("2.0"), # 2% drop triggers safety order
        safety_order_step_scale=Decimal("1.5"),    # Each safety order 1.5x further down
        safety_order_volume_scale=Decimal("1.2"),  # Each safety order 1.2x larger
        take_profit_percentage=Decimal("1.5"),     # 1.5% profit target
        stop_loss_percentage=Decimal("15.0"),      # 15% stop loss
    )

    # 2. Define the main Strategy Configuration
    strategy_config = StrategyConfig(
        type=StrategyType.DCA,
        symbol="BTC/USDT",
        dca_config=dca_config,
    )

    # 3. Instantiate the HistoricalDataSimulator
    exchange = HistoricalDataSimulator(
        csv_file="/workspaces/pv2/ccxt_binance_BTCUSDT_1h_100.csv",  # Using smaller dataset for DCA test
        api_key="test", 
        api_secret="test"
    )

    # 4. Instantiate the DCAStrategy
    strategy = DCAStrategy(
        config=strategy_config,
        exchange=exchange
    )

    # 5. Run the backtest with historical data
    print("Starting DCA strategy backtest with historical data...")
    max_iterations = 100  # Test through 100 hours of data
    iteration_count = 0
    last_log_time = datetime.now()
    start_balance_usdt = None
    start_balance_btc = None
    
    try:
        while iteration_count < max_iterations and exchange.current_index < exchange.max_index:
            iteration_count += 1
            
            # Log progress every 15 iterations
            if iteration_count % 15 == 0:
                current_time = datetime.now()
                elapsed = (current_time - last_log_time).total_seconds()
                print(f"\n--- Iteration {iteration_count}/{max_iterations} (took {elapsed:.2f}s for last 15 iterations) ---")
                last_log_time = current_time
                
                # Show current balances
                balances = await exchange.get_balances()
                current_balances = {b.asset: float(b.free) for b in balances}
                print(f"Current balances: {current_balances}")
                
                # Store initial balances for comparison
                if start_balance_usdt is None:
                    start_balance_usdt = current_balances.get('USDT', 0)
                    start_balance_btc = current_balances.get('BTC', 0)
                
                # Show open orders
                open_orders = await exchange.get_open_orders()
                print(f"Open orders: {len(open_orders)}")
                
                # Show current market timestamp and price
                current_ts = exchange.get_current_timestamp()
                print(f"Current time in backtest: {current_ts}")
                print(f"Market price: ${exchange._last_price}")
                
                # Show DCA strategy status
                dca_status = strategy.get_status()
                print(f"DCA Status:")
                print(f"  Entry Price: ${dca_status.get('entry_price', 'None')}")
                print(f"  Safety Orders Used: {dca_status.get('safety_orders_used', 0)}/{dca_status.get('max_safety_orders', 0)}")
                print(f"  Initialized: {dca_status.get('initialized', False)}")
            
            # Execute strategy with timeout
            try:
                await asyncio.wait_for(strategy.execute(), timeout=10.0)
            except asyncio.TimeoutError:
                print(f"⚠️  Strategy execution timed out at iteration {iteration_count}")
                break
            except Exception as e:
                print(f"❌ Strategy execution failed at iteration {iteration_count}: {e}")
                import traceback
                traceback.print_exc()
                break
            
            # Shorter delay for DCA testing
            await asyncio.sleep(0.05)

    except KeyboardInterrupt:
        print("\n🛑 Manual stop requested")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nCompleted {iteration_count} iterations")
    
    # 6. Print detailed final results
    try:
        final_balance = await exchange.fetch_balance()
        print("\n" + "="*60)
        print("🏁 DCA BACKTEST RESULTS")
        print("="*60)
        
        final_balances = {}
        print("Final Balances:")
        for asset, balance in final_balance.items():
            final_balances[asset] = float(balance.free)
            print(f"  {asset}: {balance.free:.6f}")
        
        # Calculate P&L if we have initial balances
        if start_balance_usdt is not None:
            usdt_change = final_balances.get('USDT', 0) - start_balance_usdt
            btc_change = final_balances.get('BTC', 0) - start_balance_btc
            
            print(f"\nBalance Changes:")
            print(f"  USDT: {usdt_change:+.6f}")
            print(f"  BTC: {btc_change:+.6f}")
            
            # Estimate total value change
            final_price = float(exchange._last_price)
            total_value_change = usdt_change + (btc_change * final_price)
            print(f"  Total Value Change: ${total_value_change:+.2f}")
            
            # Calculate percentage return
            initial_value = start_balance_usdt + (start_balance_btc * final_price)
            if initial_value > 0:
                percentage_return = (total_value_change / initial_value) * 100
                print(f"  Percentage Return: {percentage_return:+.2f}%")
        
        # Show trade history
        trades = exchange._trades
        if trades:
            print(f"\nTrades Executed: {len(trades)}")
            print("Recent Trades:")
            for i, trade in enumerate(trades[-10:], 1):  # Show last 10 trades
                action = "BUY" if str(trade.side).upper() == "BUY" else "SELL"
                print(f"  {i}. {action} {trade.quantity:.6f} BTC @ ${trade.price:.2f}")
        else:
            print("\n❌ No trades were executed during backtest")
        
        # Show DCA final status
        final_status = strategy.get_status()
        print(f"\nFinal DCA Strategy Status:")
        for key, value in final_status.items():
            if key not in ['is_active', 'last_execution']:
                print(f"  {key}: {value}")
            
        print("="*60)
        
    except Exception as e:
        print(f"Could not fetch final balance: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Properly close the exchange connection
    try:
        await exchange.close()
        print("✅ Exchange connection closed properly")
    except Exception as e:
        print(f"Warning: Could not close exchange: {e}")


if __name__ == "__main__":
    asyncio.run(main())
