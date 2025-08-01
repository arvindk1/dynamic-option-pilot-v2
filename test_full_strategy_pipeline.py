#!/usr/bin/env python3
"""
Comprehensive test of the complete strategy scan pipeline.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_full_pipeline():
    """Test the complete strategy scan pipeline to find where opportunities are lost."""
    
    print("=== Comprehensive Strategy Pipeline Test ===\n")
    
    try:
        # Import everything we need
        from core.orchestrator.strategy_registry import StrategyRegistry
        from core.engines.engine_registry import EngineRegistry
        from utils.config_loader import ConfigLoader
        from plugins.data.yfinance_provider import YFinanceProvider
        
        # Step 1: Initialize components
        print("1. Initializing components...")
        
        config_loader = ConfigLoader()
        engine_registry = EngineRegistry()
        
        # Add data provider to engine registry
        data_provider = YFinanceProvider()
        await data_provider.initialize()
        engine_registry.register_data_provider('yfinance', data_provider)
        
        # Initialize strategy registry
        strategy_registry = StrategyRegistry(config_loader, engine_registry)
        await strategy_registry.initialize()
        
        available_strategies = strategy_registry.get_all_strategy_ids()
        print(f"   ✅ {len(available_strategies)} strategies loaded: {available_strategies[:3]}...")
        
        # Step 2: Test individual strategy
        strategy_id = 'ThetaCropWeekly'
        print(f"\n2. Testing strategy: {strategy_id}")
        
        strategy = strategy_registry.get_strategy(strategy_id)
        if not strategy:
            print(f"   ❌ Strategy {strategy_id} not found")
            return
            
        print(f"   ✅ Strategy loaded: {strategy.json_config.strategy_name}")
        print(f"   - Strategy type: {strategy.json_config.strategy_type}")
        print(f"   - Universe: {strategy.json_config.universe.get('primary_symbols', [])}")
        
        # Step 3: Test data provider integration
        print(f"\n3. Testing data provider integration...")
        universe = ['SPY']  # Test with just SPY
        
        for symbol in universe:
            try:
                quote = await data_provider.get_quote(symbol)
                print(f"   ✅ {symbol}: ${quote.price} (volume: {quote.volume})")
                
                # Test strategy's entry signals check
                config = strategy.json_config.get_effective_config()
                passes_signals = await strategy._passes_entry_signals(symbol, quote, config)
                print(f"   - Entry signals check: {'✅ PASS' if passes_signals else '❌ FAIL'}")
                
                if not passes_signals:
                    # Debug entry signals
                    entry_signals = config.get('entry_signals', {})
                    print(f"   - Entry signals config: {entry_signals}")
                    
                    # Check each filter
                    if 'price_range' in entry_signals:
                        price_range = entry_signals['price_range']
                        min_p = price_range.get('min', 0)
                        max_p = price_range.get('max', float('inf'))
                        price_ok = min_p <= quote.price <= max_p
                        print(f"     * Price range [{min_p}-{max_p}]: {'✅' if price_ok else '❌'} (actual: ${quote.price})")
                    
                    if 'min_volume' in entry_signals:
                        min_vol = entry_signals['min_volume']
                        vol_ok = quote.volume >= min_vol if quote.volume > 0 else True
                        print(f"     * Min volume {min_vol}: {'✅' if vol_ok else '❌'} (actual: {quote.volume})")
                
                # Test opportunity generation even if signals fail
                print(f"   - Testing opportunity generation...")
                symbol_opportunities = await strategy._scan_symbol(symbol, data_provider, config)
                print(f"   - Opportunities generated: {len(symbol_opportunities)}")
                
                if symbol_opportunities:
                    opp = symbol_opportunities[0]
                    print(f"     * Sample opportunity: {opp.symbol} {opp.strategy_name}")
                    print(f"       Premium: ${opp.premium_collected}, Max Loss: ${opp.max_loss}")
                    print(f"       Probability: {opp.probability_of_profit:.1%}")
                else:
                    # Try manual opportunity creation
                    print(f"   - Testing manual opportunity creation...")
                    manual_opp = await strategy._create_opportunity(symbol, quote, config, 0)
                    if manual_opp:
                        print(f"     ✅ Manual opportunity created successfully")
                        print(f"       Strategy: {manual_opp.strategy_name}")
                        print(f"       Premium: ${manual_opp.premium_collected}")
                        print(f"       Max Loss: ${manual_opp.max_loss}")
                    else:
                        print(f"     ❌ Manual opportunity creation failed")
                
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
        # Step 4: Test complete scan_opportunities method
        print(f"\n4. Testing complete scan_opportunities method...")
        try:
            all_opportunities = await strategy.scan_opportunities(universe, max_opportunities=5)
            print(f"   ✅ Complete scan returned {len(all_opportunities)} opportunities")
            
            for i, opp in enumerate(all_opportunities[:3]):
                print(f"   - Opportunity {i+1}: {opp.symbol} ${opp.premium_collected:.2f} premium")
                print(f"     Probability: {opp.probability_of_profit:.1%}, Score: {getattr(opp, 'score', 'N/A')}")
                
        except Exception as e:
            print(f"   ❌ Complete scan failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ Pipeline test completed!")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())