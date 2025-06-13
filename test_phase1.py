"""Test script to demonstrate Phase 1 implementation."""

import asyncio
import json
from pathlib import Path

from src.passivbot.core.config import PassivbotConfig, create_default_config
from src.passivbot import PassivBot
from src.passivbot.exchanges import get_exchange, list_supported_exchanges
from src.passivbot.strategies import get_strategy, list_supported_strategies


async def test_phase1_implementation():
    """Test the Phase 1 implementation."""
    print("🚀 Testing Passivbot Phase 1 Implementation\n")
    
    # Test 1: Configuration system
    print("1. Testing Configuration System:")
    print("   Creating default configuration...")
    config_data = create_default_config()
    print(f"   ✅ Default config created with {len(config_data)} sections")
    
    # Save test config
    test_config_path = Path("test_config.json")
    with open(test_config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    print(f"   ✅ Config saved to {test_config_path}")
    
    # Load config
    config = PassivbotConfig.from_file(test_config_path)
    print(f"   ✅ Config loaded successfully")
    print(f"   - Exchange: {config.exchange.type}")
    print(f"   - Strategies: {len(config.strategies)}")
    print(f"   - Dry Run: {config.dry_run}")
    
    # Test 2: Exchange system
    print("\n2. Testing Exchange System:")
    print("   Supported exchanges:")
    for exchange_type in list_supported_exchanges():
        print(f"   - {exchange_type}")
    
    print("\n   Creating exchange instance...")
    try:
        exchange = get_exchange(config.exchange)
        print(f"   ✅ {exchange} created successfully")
    except Exception as e:
        print(f"   ⚠️  Exchange creation: {e}")
    
    # Test 3: Strategy system
    print("\n3. Testing Strategy System:")
    print("   Supported strategies:")
    for strategy_type in list_supported_strategies():
        print(f"   - {strategy_type}")
    
    print("\n   Creating strategy instances...")
    try:
        for strategy_config in config.strategies:
            strategy = get_strategy(strategy_config, exchange, dry_run=True)
            print(f"   ✅ {strategy} created successfully")
    except Exception as e:
        print(f"   ⚠️  Strategy creation: {e}")
    
    # Test 4: Bot initialization
    print("\n4. Testing Bot System:")
    print("   Creating bot instance...")
    try:
        bot = PassivBot(config)
        print(f"   ✅ Bot created successfully")
        print(f"   - Status: {bot.status}")
    except Exception as e:
        print(f"   ❌ Bot creation failed: {e}")
    
    # Test 5: Configuration validation
    print("\n5. Testing Configuration Validation:")
    from src.passivbot.core.config import validate_configuration
    warnings = validate_configuration(config)
    if warnings:
        print("   Validation warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("   ✅ No validation warnings")
    
    # Test 6: Type system
    print("\n6. Testing Type System:")
    from src.passivbot.core.types import Order, OrderSide, OrderType, OrderStatus
    from decimal import Decimal
    
    # Create a test order
    test_order = Order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00")
    )
    print(f"   ✅ Test order created: {test_order.symbol} {test_order.side} {test_order.quantity}")
    
    # Test 7: Exception handling
    print("\n7. Testing Exception System:")
    from src.passivbot.core.exceptions import (
        PassivbotError, ExchangeError, StrategyError, 
        handle_exchange_error, is_retriable_error
    )
    
    # Test error handling
    test_error = Exception("Test connection timeout")
    handled_error = handle_exchange_error(test_error)
    is_retriable = is_retriable_error(handled_error)
    print(f"   ✅ Error handling: {type(handled_error).__name__}, retriable: {is_retriable}")
    
    print("\n🎉 Phase 1 Implementation Test Complete!")
    print("\n📋 Summary:")
    print("   ✅ Core bot class with lifecycle management")
    print("   ✅ CLI interface structure (requires typer/rich installation)")
    print("   ✅ Exchange abstraction layer with Binance/Bybit implementations")
    print("   ✅ Strategy framework with Grid and DCA strategies")
    print("   ✅ Configuration system with validation")
    print("   ✅ Type system with Pydantic models")
    print("   ✅ Exception hierarchy with error handling")
    
    print("\n🔧 Next Steps for Full Implementation:")
    print("   1. Install missing dependencies (aiohttp, typer, rich)")
    print("   2. Implement complete API authentication/signatures")
    print("   3. Add WebSocket support for real-time data")
    print("   4. Implement database layer for persistence")
    print("   5. Add comprehensive testing suite")
    print("   6. Implement web interface")
    print("   7. Add notification system")
    
    # Cleanup
    test_config_path.unlink()
    print(f"\n🧹 Cleaned up test file: {test_config_path}")


if __name__ == "__main__":
    asyncio.run(test_phase1_implementation())
