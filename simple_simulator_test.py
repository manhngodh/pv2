import asyncio
import logging
from decimal import Decimal
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

from passivbot.exchanges.simulator import SimulatorExchange
from passivbot.core.types import OrderSide, OrderType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Run simple simulator test with manual orders."""
    
    # Initialize simulator with ccxt data
    exchange = SimulatorExchange(
        api_key="test", 
        api_secret="test",
        ccxt_exchange="binance",
        ccxt_symbol="BTC/USDT",
        ccxt_timeframe="1h",
        ccxt_limit=100  # Get 100 hours of data
    )
    
    symbol = "BTC/USDT"
    prices = []
    balances = []
    timestamps = []
    
    # Initial balance
    balance = await exchange.get_balance("USDT")
    initial_balance = balance.free if balance else Decimal("10000")
    logger.info(f"Initial USDT balance: {initial_balance}")
    
    # Simulate market data and trading over time
    try:
        for i in range(50):  # Process 50 time periods
            # Get market data (advances the time in simulation)
            market_data = await exchange.get_market_data(symbol)
            prices.append(float(market_data.price))
            timestamps.append(market_data.timestamp)
            
            # Simple trading logic - buy low, sell high
            # Buy if price drops 1% from the first price
            if i > 0 and prices[i] < prices[0] * 0.99:
                logger.info(f"Price dropped to {market_data.price}, placing buy order")
                order = await exchange.place_order(
                    symbol=symbol,
                    side=OrderSide.BUY,  # Using enum value 
                    order_type=OrderType.MARKET,  # Using enum value
                    quantity=Decimal("0.1"),
                    price=None  # Market order
                )
                logger.info(f"Placed order: {order.id} - {order.status}")
            
            # Sell if price rises 1% from the first price
            if i > 0 and prices[i] > prices[0] * 1.01:
                logger.info(f"Price rose to {market_data.price}, placing sell order")
                order = await exchange.place_order(
                    symbol=symbol,
                    side=OrderSide.SELL,  # Using enum value
                    order_type=OrderType.MARKET,  # Using enum value 
                    quantity=Decimal("0.1"),
                    price=None  # Market order
                )
                logger.info(f"Placed order: {order.id} - {order.status}")
            
            # Track balance changes
            balance = await exchange.get_balance("USDT")
            current_balance = balance.free if balance else Decimal("0")
            balances.append(float(current_balance))
    
    except StopIteration:
        logger.info("Reached end of historical data")
    
    # Calculate final results
    final_balance = await exchange.get_balance("USDT")
    final_btc = await exchange.get_balance("BTC")
    
    logger.info("\n----- Simulation Results -----")
    logger.info(f"Initial balance: {initial_balance} USDT")
    logger.info(f"Final balance: {final_balance.free} USDT")
    logger.info(f"Final BTC: {final_btc.free if final_btc else 0} BTC")
    
    # Calculate profit/loss
    btc_value = final_btc.free * prices[-1] if final_btc else Decimal("0") 
    total_value = final_balance.free + btc_value
    profit_loss = total_value - initial_balance
    roi = (profit_loss / initial_balance) * 100
    
    logger.info(f"Profit/Loss: {profit_loss} USDT ({roi:.2f}%)")
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Price chart
    ax1 = plt.subplot(211)
    ax1.plot([t.timestamp() for t in timestamps], prices, label='BTC/USDT Price')
    ax1.set_ylabel('Price (USDT)')
    ax1.set_title('BTC/USDT Price')
    ax1.grid(True)
    
    # Balance chart
    ax2 = plt.subplot(212)
    ax2.plot([t.timestamp() for t in timestamps], balances, label='USDT Balance', color='green')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Balance (USDT)')
    ax2.set_title('Account Balance')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('simulation_results.png')
    logger.info("Results chart saved as 'simulation_results.png'")

if __name__ == "__main__":
    asyncio.run(main())
