#!/usr/bin/env python3
"""
Test script to diagnose why strategy scans return 0 opportunities.
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from plugins.data.yfinance_provider import YFinanceProvider
from core.interfaces.data_provider_interface import Quote

async def test_opportunity_generation():
    """Test the opportunity generation pipeline step by step."""
    
    print("=== Testing Opportunity Generation Pipeline ===\n")
    
    # Step 1: Test data provider
    print("1. Testing data provider...")
    try:
        provider = YFinanceProvider()
        quote = await provider.get_quote('SPY')
        print(f"   ✅ SPY quote: ${quote.price} (volume: {quote.volume})")
    except Exception as e:
        print(f"   ❌ Data provider failed: {e}")
        return
    
    # Step 2: Test JSON config loading
    print("\n2. Testing JSON config loading...")
    try:
        with open('backend/config/strategies/rules/ThetaCropWeekly.json', 'r') as f:
            config = json.load(f)
        print(f"   ✅ ThetaCrop config loaded: {config['strategy_name']}")
        print(f"   - Strategy type: {config.get('strategy_type', 'N/A')}")
        print(f"   - Universe symbols: {config.get('universe', {}).get('primary_symbols', [])}")
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
        return
    
    # Step 3: Test entry signals manually
    print("\n3. Testing entry signals...")
    entry_signals = config.get('entry_signals', {})
    print(f"   - Entry signals config: {entry_signals}")
    
    # Check price range
    price_range = entry_signals.get('price_range', {})
    min_price = price_range.get('min', 0)
    max_price = price_range.get('max', float('inf'))
    passes_price = min_price <= quote.price <= max_price
    print(f"   - Price range [{min_price}-{max_price}]: {'✅' if passes_price else '❌'} (SPY: ${quote.price})")
    
    # Check volume
    min_volume = entry_signals.get('min_volume', 0)
    passes_volume = quote.volume >= min_volume if quote.volume > 0 else True
    print(f"   - Min volume {min_volume}: {'✅' if passes_volume else '❌'} (SPY: {quote.volume})")
    
    # Step 4: Test opportunity creation
    print("\n4. Testing opportunity creation...")
    
    try:
        # Simulate the opportunity creation logic
        position_params = config.get('position_parameters', {})
        strategy_type = config.get('strategy_type', 'UNKNOWN')
        
        print(f"   - Strategy type: {strategy_type}")
        print(f"   - Position params: {position_params}")
        
        # Test the logic from _create_opportunity
        if strategy_type == 'IRON_CONDOR':
            delta_target = position_params.get('delta_target', 0.20)
            short_strike_call = quote.price * (1 + delta_target)
            short_strike_put = quote.price * (1 - delta_target)
            wing_width = position_params.get('wing_widths', [5, 10])[0]
            
            premium = 2.0
            max_loss = wing_width * 100 - premium * 100
            
            print(f"   ✅ Iron Condor opportunity:")
            print(f"      - Short Call: ${short_strike_call:.2f}")
            print(f"      - Short Put: ${short_strike_put:.2f}")
            print(f"      - Wing Width: ${wing_width}")
            print(f"      - Premium: ${premium}")
            print(f"      - Max Loss: ${max_loss}")
            
        else:
            print(f"   ❌ Strategy type '{strategy_type}' not handled in test")
            
    except Exception as e:
        print(f"   ❌ Opportunity creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Test with multiple strategies
    print("\n5. Testing multiple strategies...")
    strategy_files = [
        'ThetaCropWeekly.json',
        'IronCondor.json', 
        'RSICouponStrategy.json'
    ]
    
    for strategy_file in strategy_files:
        try:
            with open(f'backend/config/strategies/rules/{strategy_file}', 'r') as f:
                strat_config = json.load(f)
            
            strategy_type = strat_config.get('strategy_type', 'UNKNOWN')
            universe = strat_config.get('universe', {}).get('primary_symbols', ['SPY'])
            
            # Simple pass/fail for entry signals
            entry_signals = strat_config.get('entry_signals', {})
            should_pass = True
            
            if 'price_range' in entry_signals:
                price_range = entry_signals['price_range']
                min_p = price_range.get('min', 0)
                max_p = price_range.get('max', float('inf'))
                should_pass = should_pass and (min_p <= quote.price <= max_p)
            
            print(f"   - {strat_config['strategy_name']} ({strategy_type}): {'✅' if should_pass else '❌'}")
            print(f"     Universe: {universe}")
            
        except Exception as e:
            print(f"   - {strategy_file}: ❌ Error loading: {e}")

if __name__ == "__main__":
    asyncio.run(test_opportunity_generation())