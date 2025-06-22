import asyncio
import logging
import signal
import sys
from decimal import Decimal
from datetime import datetime

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

async def main():
    """
    Main function to set up and run the grid strategy backtest.
    """
    # 1. Define the Grid Strategy Configuration
    # Using more realistic price range around current market price
    grid_config = GridConfig(
        num_levels=10,
        quantity_percentage=Decimal("10"),  # 10% of quote balance per grid level
        price_spacing_percentage=Decimal("0.5"), # 0.5% spacing for tighter grid
        lower_price=Decimal("100000"),  # Lower bound around current price
        upper_price=Decimal("108000"),  # Upper bound around current price
    )

    # 2. Define the main Strategy Configuration
    strategy_config = StrategyConfig(
        type=StrategyType.GRID,
        symbol="BTC/USDT",
        grid_config=grid_config,
    )

    # 3. Instantiate the SimulatorExchange with ccxt data
    # This will fetch data from Binance for BTC/USDT and cache it locally.
    exchange = SimulatorExchange(
        api_key="test", 
        api_secret="test",
        ccxt_exchange="binance",
        ccxt_symbol="BTC/USDT",
        ccxt_timeframe="1h",
        ccxt_limit=500  # Fetch more data for better simulation
    )

    # 4. Instantiate the GridStrategy
    strategy = GridStrategy(
        config=strategy_config,
        exchange=exchange
    )

    # 5. Run the simulation loop with better control
    print("Starting strategy backtest...")
    max_iterations = 100  # Limit iterations to prevent infinite loop
    iteration_count = 0
    last_log_time = datetime.now()
    
    try:
        while iteration_count < max_iterations:
            iteration_count += 1
            
            # Log progress every 10 iterations
            if iteration_count % 10 == 0:
                current_time = datetime.now()
                elapsed = (current_time - last_log_time).total_seconds()
                print(f"Iteration {iteration_count}/{max_iterations} (took {elapsed:.2f}s for last 10 iterations)")
                last_log_time = current_time
                
                # Show current balances
                balances = await exchange.get_balances()
                print(f"Current balances: {[(b.asset, float(b.free)) for b in balances]}")
                
                # Show open orders
                open_orders = await exchange.get_open_orders()
                print(f"Open orders: {len(open_orders)}")
            
            # Execute strategy with timeout
            try:
                await asyncio.wait_for(strategy.execute(), timeout=5.0)
            except asyncio.TimeoutError:
                print(f"⚠️  Strategy execution timed out at iteration {iteration_count}")
                break
            except Exception as e:
                print(f"❌ Strategy execution failed at iteration {iteration_count}: {e}")
                break
            
            # Add a small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Manual stop requested")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nCompleted {iteration_count} iterations")
    
    # 6. Print final results (optional)
    try:
        final_balance = await exchange.fetch_balance()
        print("\n----- Backtest Results -----")
        print("Final Balances:")
        for asset, balance in final_balance.items():
            print(f"  {asset}: {balance.free:.4f}")
        print("--------------------------")
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
