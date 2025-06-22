import asyncio
import logging
import signal
import sys
import pandas as pd
from decimal import Decimal
from datetime import datetime
from typing import Iterator

from passivbot.core.config import StrategyConfig, GridConfig
from passivbot.core.types import StrategyType
from passivbot.exchanges.simulator import SimulatorExchange
from passivbot.strategies.grid import GridStrategy

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
        if self.current_index % 10 == 0:
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
    Main function to set up and run the grid strategy backtest with historical data.
    """
    print("🚀 Starting Historical Backtest")
    
    # 1. Define the Grid Strategy Configuration
    # Using dynamic price range based on historical data
    grid_config = GridConfig(
        num_levels=10,
        quantity_percentage=Decimal("5"),  # 5% of quote balance per grid level (more conservative)
        price_spacing_percentage=Decimal("0.3"), # 0.3% spacing for tighter grid
        lower_price=Decimal("104000"),  # Will be adjusted based on data
        upper_price=Decimal("107000"),  # Will be adjusted based on data
    )

    # 2. Define the main Strategy Configuration
    strategy_config = StrategyConfig(
        type=StrategyType.GRID,
        symbol="BTC/USDT",
        grid_config=grid_config,
    )

    # 3. Instantiate the HistoricalDataSimulator
    exchange = HistoricalDataSimulator(
        csv_file="/workspaces/pv2/ccxt_binance_BTCUSDT_1h_500.csv",
        api_key="test", 
        api_secret="test"
    )

    # 4. Instantiate the GridStrategy
    strategy = GridStrategy(
        config=strategy_config,
        exchange=exchange
    )

    # 5. Run the backtest with historical data
    print("Starting strategy backtest with historical data...")
    max_iterations = 200  # More iterations to go through historical data
    iteration_count = 0
    last_log_time = datetime.now()
    start_balance_usdt = None
    start_balance_btc = None
    
    try:
        while iteration_count < max_iterations and exchange.current_index < exchange.max_index:
            iteration_count += 1
            
            # Log progress every 20 iterations
            if iteration_count % 20 == 0:
                current_time = datetime.now()
                elapsed = (current_time - last_log_time).total_seconds()
                print(f"\n--- Iteration {iteration_count}/{max_iterations} (took {elapsed:.2f}s for last 20 iterations) ---")
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
                
                # Show current market timestamp
                current_ts = exchange.get_current_timestamp()
                print(f"Current time in backtest: {current_ts}")
                print(f"Market price: ${exchange._last_price}")
            
            # Execute strategy with timeout
            try:
                await asyncio.wait_for(strategy.execute(), timeout=10.0)
            except asyncio.TimeoutError:
                print(f"⚠️  Strategy execution timed out at iteration {iteration_count}")
                break
            except Exception as e:
                print(f"❌ Strategy execution failed at iteration {iteration_count}: {e}")
                break
            
            # Shorter delay since we're using historical data
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
        print("\n" + "="*50)
        print("🏁 BACKTEST RESULTS")
        print("="*50)
        
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
            
            # Estimate total value change (rough calculation)
            final_price = float(exchange._last_price)
            total_value_change = usdt_change + (btc_change * final_price)
            print(f"  Total Value Change: ${total_value_change:+.2f}")
        
        # Show trade history
        trades = exchange._trades
        if trades:
            print(f"\nTrades Executed: {len(trades)}")
            for i, trade in enumerate(trades[-5:], 1):  # Show last 5 trades
                print(f"  {i}. {trade.side} {trade.quantity} @ ${trade.price}")
        else:
            print("\nNo trades were executed during backtest")
            
        print("="*50)
        
    except Exception as e:
        print(f"Could not fetch final balance: {e}")
    
    # 7. Properly close the exchange connection
    try:
        await exchange.close()
        print("✅ Exchange connection closed properly")
    except Exception as e:
        print(f"Warning: Could not close exchange: {e}")


if __name__ == "__main__":
    asyncio.run(main())
