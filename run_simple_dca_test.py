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
    Simple DCA strategy test with minimal iterations.
    """
    print("🚀 Starting Simple DCA Strategy Test")
    
    # 1. Simple DCA Configuration
    dca_config = DCAConfig(
        base_order_size=Decimal("100"),        # $100 initial buy
        safety_order_size=Decimal("50"),       # $50 safety orders
        max_safety_orders=3,                   # Only 3 safety orders
        price_deviation_percentage=Decimal("2.0"), # 2% drop triggers safety order
        safety_order_step_scale=Decimal("1.5"),    # Each safety order 1.5x further down
        safety_order_volume_scale=Decimal("1.2"),  # Each safety order 1.2x larger
        take_profit_percentage=Decimal("1.5"),     # 1.5% profit target
        stop_loss_percentage=Decimal("10.0"),      # 10% stop loss
    )

    # 2. Strategy Configuration
    strategy_config = StrategyConfig(
        type=StrategyType.DCA,
        symbol="BTC/USDT",
        dca_config=dca_config,
    )

    # 3. Simulator with limited data
    exchange = HistoricalDataSimulator(
        csv_file="/workspaces/pv2/ccxt_binance_BTCUSDT_1h_100.csv",
        api_key="test", 
        api_secret="test"
    )

    # 4. DCA Strategy
    strategy = DCAStrategy(
        config=strategy_config,
        exchange=exchange
    )

    # 5. Simple test loop
    print("Starting simple DCA test...")
    max_iterations = 30  # Just 30 iterations
    iteration_count = 0
    
    try:
        while iteration_count < max_iterations and exchange.current_index < exchange.max_index:
            iteration_count += 1
            
            # Show progress every 10 iterations
            if iteration_count % 10 == 0:
                print(f"\n--- Iteration {iteration_count}/{max_iterations} ---")
                
                # Show current balances
                balances = await exchange.get_balances()
                current_balances = {b.asset: float(b.free) for b in balances}
                print(f"Current balances: {current_balances}")
                
                # Show open orders
                open_orders = await exchange.get_open_orders()
                print(f"Open orders: {len(open_orders)}")
                
                # Show market info
                print(f"Market price: ${exchange._last_price}")
                
                # Show DCA info
                print(f"DCA Position Size: {strategy._position_size}")
                print(f"DCA Entry Price: {strategy._entry_price}")
                print(f"DCA Initialized: {strategy._initialized}")
            
            # Execute strategy
            try:
                await asyncio.wait_for(strategy.execute(), timeout=5.0)
            except Exception as e:
                print(f"❌ Strategy execution failed at iteration {iteration_count}: {e}")
                break
            
            # Small delay
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Manual stop requested")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nCompleted {iteration_count} iterations")
    
    # Show final results
    try:
        final_balance = await exchange.fetch_balance()
        print("\n" + "="*50)
        print("🏁 SIMPLE DCA TEST RESULTS")
        print("="*50)
        
        print("Final Balances:")
        for asset, balance in final_balance.items():
            print(f"  {asset}: {balance.free:.6f}")
        
        # Show trades
        trades = exchange._trades
        if trades:
            print(f"\nTrades Executed: {len(trades)}")
            for i, trade in enumerate(trades, 1):
                action = "BUY" if str(trade.side).upper() == "BUY" else "SELL"
                print(f"  {i}. {action} {trade.quantity:.6f} BTC @ ${trade.price:.2f}")
        else:
            print("\n❌ No trades executed")
            
        print("="*50)
        
    except Exception as e:
        print(f"Could not fetch final balance: {e}")
    
    # Close exchange
    try:
        await exchange.close()
        print("✅ Exchange connection closed properly")
    except Exception as e:
        print(f"Warning: Could not close exchange: {e}")


if __name__ == "__main__":
    asyncio.run(main())
