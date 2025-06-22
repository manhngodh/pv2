"""A simulated exchange for backtesting and development using real market data."""

import asyncio
import random
import math
from decimal import Decimal
from typing import Dict, List, Optional, Any
import ccxt.async_support as ccxt

from passivbot.core.types import (
    Order, Ticker, Trade, Balance, Position, MarketData, 
    OrderSide, OrderType, OrderStatus
)
from .base import BaseExchange


class SimulatorExchange(BaseExchange):
    """Simulated exchange for testing purposes using real market data."""

    def __init__(self, api_key: str = '', api_secret: str = '', exchange_name: str = 'binance', **kwargs):
        # Create a mock config if not provided
        from passivbot.core.config import ExchangeConfig
        from passivbot.core.types import ExchangeType
        
        config = kwargs.get('config') or ExchangeConfig(
            type=ExchangeType.SIMULATOR,
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,
            rate_limit=10
        )
        super().__init__(config)
        self._balances: Dict[str, Decimal] = {
            "USDT": Decimal("10000"),
            "BTC": Decimal("10"),
        }
        self._last_price = Decimal("25000")
        self._orders: List[Order] = []
        self._trades: List[Trade] = []
        
        # Initialize ccxt exchange for real data
        self.exchange_name = exchange_name
        exchange_class = getattr(ccxt, exchange_name)
        self.ccxt_exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'sandbox': kwargs.get('sandbox', True),  # Use testnet by default
            **kwargs
        })
        
        # Simulation parameters (for order processing simulation)
        self.slippage = Decimal(kwargs.get("slippage", "0.001"))  # 0.1% slippage simulation
        self.trading_fee_rate = Decimal(kwargs.get("trading_fee", "0.001"))  # 0.1% trading fee

    async def fetch_ticker(self, symbol: str) -> Ticker:
        """Fetch real ticker price from exchange."""
        try:
            # Add timeout to prevent hanging
            ticker_data = await asyncio.wait_for(
                self.ccxt_exchange.fetch_ticker(symbol), 
                timeout=3.0
            )
            self._last_price = Decimal(str(ticker_data['last']))
            return Ticker(
                symbol=symbol, 
                price=self._last_price,
                bid=Decimal(str(ticker_data.get('bid', 0))) if ticker_data.get('bid') else None,
                ask=Decimal(str(ticker_data.get('ask', 0))) if ticker_data.get('ask') else None,
                volume=Decimal(str(ticker_data.get('baseVolume', 0))) if ticker_data.get('baseVolume') else None
            )
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout fetching ticker for {symbol}, using cached price: {self._last_price}")
            return Ticker(symbol=symbol, price=self._last_price)
        except Exception as e:
            # Fallback to last known price if fetch fails
            print(f"❌ Failed to fetch ticker for {symbol}: {e}")
            return Ticker(symbol=symbol, price=self._last_price)

    async def create_order(self, symbol: str, type: str, side: str, amount: Decimal, price: Optional[Decimal] = None) -> Order:
        """Create a new order (legacy method)."""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide(side),
            order_type=OrderType(type),
            quantity=amount,
            price=price
        )

    async def fetch_balance(self) -> Dict[str, Balance]:
        """Fetch account balance."""
        result = {}
        for asset, amount in self._balances.items():
            # Ensure balance is not negative (should not happen in real trading)
            free_amount = max(amount, Decimal("0"))
            result[asset] = Balance(asset=asset, free=free_amount, locked=Decimal("0"))
        return result

    async def close(self):
        """Close the ccxt exchange connection."""
        if self.ccxt_exchange:
            await self.ccxt_exchange.close()

    async def _process_order(self, order: Order):
        """Process an order in the background with realistic simulation."""
        print(f"🔄 Processing order {order.id} ({order.side} {order.quantity} {order.symbol} @ {order.price})")
        
        await asyncio.sleep(0.1)  # Simulate network latency
        
        # Get current market price for more realistic execution
        try:
            ticker = await self.fetch_ticker(order.symbol)
            current_price = ticker.price
            print(f"📊 Current market price for {order.symbol}: {current_price}")
        except Exception as e:
            print(f"⚠️  Using cached price for order processing: {self._last_price}")
            current_price = self._last_price
        
        # Simulate order execution logic
        should_execute = False
        execution_price = current_price
        
        if order.type == OrderType.MARKET:
            should_execute = True
            # Apply slippage for market orders
            if order.side == OrderSide.BUY:
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)
            print(f"📈 Market order will execute at {execution_price} (slippage applied)")
        elif order.price and order.type == OrderType.LIMIT:
            if (order.side == OrderSide.BUY and order.price >= current_price) or \
               (order.side == OrderSide.SELL and order.price <= current_price):
                should_execute = True
                execution_price = order.price
                print(f"✅ Limit order conditions met, will execute at {execution_price}")
            else:
                print(f"⏳ Limit order conditions not met (order: {order.price}, market: {current_price})")
        
        if should_execute:
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_price = execution_price
            
            trade = Trade(
                id=str(len(self._trades) + 1),
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                price=execution_price,
                quantity=order.quantity,
                fee=order.quantity * Decimal("0.001"),
                fee_asset="USDT"
            )
            self._trades.append(trade)
            
            # Update balances
            base, quote = order.symbol.split("/")
            if order.side == OrderSide.BUY:
                # Buying: Pay quote currency, receive base currency
                cost = order.quantity * execution_price
                fee = cost * self.trading_fee_rate
                total_cost = cost + fee
                
                self._balances[base] = self._balances.get(base, Decimal("0")) + order.quantity
                self._balances[quote] = self._balances.get(quote, Decimal("0")) - total_cost
            else:
                # Selling: Give base currency, receive quote currency
                revenue = order.quantity * execution_price
                fee = revenue * self.trading_fee_rate
                net_revenue = revenue - fee
                
                self._balances[base] = self._balances.get(base, Decimal("0")) - order.quantity
                self._balances[quote] = self._balances.get(quote, Decimal("0")) + net_revenue
            
            print(f"✅ Order {order.id} executed: {order.side} {order.quantity} @ {execution_price}")
            print(f"📊 Updated balances: BTC={self._balances.get('BTC', 0):.6f}, USDT={self._balances.get('USDT', 0):.2f}")
        else:
            order.status = OrderStatus.OPEN
            print(f"⏳ Order {order.id} remains open")

    # Abstract method implementations
    async def connect(self) -> None:
        """Connect to the exchange."""
        self._connected = True
        print(f"Connected to {self.exchange_name} simulator")

    async def disconnect(self) -> None:
        """Disconnect from the exchange."""
        if self.ccxt_exchange:
            await self.ccxt_exchange.close()
        self._connected = False
        print(f"Disconnected from {self.exchange_name} simulator")

    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        balances = []
        for asset, amount in self._balances.items():
            # Ensure balance is not negative (should not happen in real trading)
            free_amount = max(amount, Decimal("0"))
            balances.append(Balance(asset=asset, free=free_amount, locked=Decimal("0")))
        return balances

    async def get_balance(self, asset: str) -> Optional[Balance]:
        """Get balance for specific asset."""
        if asset in self._balances:
            return Balance(asset=asset, free=self._balances[asset], locked=Decimal("0"))
        return None

    async def get_positions(self) -> List[Position]:
        """Get open positions."""
        # For spot trading simulator, return empty positions
        return []

    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol."""
        # For spot trading simulator, return None
        return None

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        client_id: Optional[str] = None,
        **kwargs
    ) -> Order:
        """Place a trading order."""
        order_id = client_id or str(len(self._orders) + 1)
        order = Order(
            id=order_id,
            client_id=order_id,
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            price=price or self._last_price,
            status=OrderStatus.PENDING
        )
        self._orders.append(order)
        # Simulate order execution
        asyncio.create_task(self._process_order(order))
        return order

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        for order in self._orders:
            if order.id == order_id and order.symbol == symbol:
                if order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                    order.status = OrderStatus.CANCELLED
                    return True
        return False

    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order details."""
        for order in self._orders:
            if order.id == order_id and order.symbol == symbol:
                return order
        return None

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders."""
        open_orders = [
            order for order in self._orders 
            if order.status in [OrderStatus.PENDING, OrderStatus.OPEN]
        ]
        if symbol:
            open_orders = [order for order in open_orders if order.symbol == symbol]
        return open_orders

    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data for symbol."""
        ticker = await self.fetch_ticker(symbol)
        return MarketData(
            symbol=symbol,
            price=ticker.price,
            bid=ticker.bid,
            ask=ticker.ask,
            volume_24h=ticker.volume
        )

    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for symbol."""
        try:
            # Add timeout to prevent hanging
            orderbook = await asyncio.wait_for(
                self.ccxt_exchange.fetch_order_book(symbol, limit),
                timeout=3.0
            )
            return orderbook
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout fetching orderbook for {symbol}, using mock data")
            # Return mock orderbook
            current_price = self._last_price
            return {
                'bids': [[float(current_price * Decimal("0.999")), 1.0]],
                'asks': [[float(current_price * Decimal("1.001")), 1.0]],
                'timestamp': None,
                'datetime': None,
                'nonce': None
            }
        except Exception as e:
            print(f"❌ Failed to fetch orderbook for {symbol}: {e}")
            # Return mock orderbook
            current_price = self._last_price
            return {
                'bids': [[float(current_price * Decimal("0.999")), 1.0]],
                'asks': [[float(current_price * Decimal("1.001")), 1.0]],
                'timestamp': None,
                'datetime': None,
                'nonce': None
            }
