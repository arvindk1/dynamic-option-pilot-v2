#!/usr/bin/env python3
"""
Force opportunity generation to test if the plugin is working.
"""

import requests
import json
import time

def test_force_opportunities():
    """Test if we can manually force opportunities to be generated."""
    
    print("=== Testing Force Opportunity Generation ===\n")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Test a specific strategy configuration
    print("1. Testing strategy configuration access...")
    try:
        response = requests.get(f"{base_url}/api/strategies/", timeout=10)
        if response.status_code == 200:
            strategies = response.json()
            strategy_list = strategies.get('strategies', [])
            
            # Find ThetaCrop strategy
            thetacrop = next((s for s in strategy_list if s['id'] == 'ThetaCropWeekly'), None)
            if thetacrop:
                print(f"   ✅ ThetaCrop strategy found: {thetacrop['name']}")
                print(f"   - Category: {thetacrop['category']}")
                print(f"   - Last scan: {thetacrop['last_scan']}")
                print(f"   - Total opportunities: {thetacrop['total_opportunities']}")
            else:
                print("   ❌ ThetaCrop strategy not found")
                return
        else:
            print(f"   ❌ Failed to get strategies: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: Test manual scan trigger
    print("\n2. Testing manual scan triggers...")
    test_strategies = ['ThetaCropWeekly', 'IronCondor', 'RSICouponStrategy']
    
    for strategy_id in test_strategies:
        print(f"\n   Testing {strategy_id}:")
        try:
            # Test quick scan
            response = requests.post(f"{base_url}/api/strategies/{strategy_id}/quick-scan", timeout=30)
            if response.status_code == 200:
                result = response.json()
                opportunities = result.get('opportunities_found', 0)
                success = result.get('success', False)
                scan_symbols = result.get('scan_symbols', [])
                
                print(f"     - Quick scan: {opportunities} opportunities")
                print(f"     - Success: {success}")
                print(f"     - Symbols: {scan_symbols}")
                
            else:
                print(f"     ❌ Quick scan failed: {response.status_code}")
                print(f"     Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Step 3: Check if any opportunities appeared in cache
    print("\n3. Checking trading opportunities cache...")
    try:
        response = requests.get(f"{base_url}/api/trading/opportunities", timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunities', [])
            total = data.get('total_count', 0)
            cache_stats = data.get('cache_stats', {}).get('stats', {})
            
            print(f"   - Total opportunities in cache: {total}")
            print(f"   - Cache stats: {cache_stats}")
            
            if opportunities:
                print(f"   ✅ Found {len(opportunities)} opportunities!")
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"     {i}. {opp.get('symbol', 'N/A')} - {opp.get('strategy_type', 'N/A')}")
                    print(f"        Premium: ${opp.get('premium', 0):.2f}")
            else:
                print(f"   ❌ No opportunities in cache")
        else:
            print(f"   ❌ Failed to get opportunities: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 4: Test scheduler trigger
    print("\n4. Testing scheduler trigger...")
    try:
        response = requests.post(f"{base_url}/api/scheduler/scan/high_probability", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Scheduler trigger successful: {result}")
            
            # Wait and check again
            print("   - Waiting 3 seconds for scan to complete...")
            time.sleep(3)
            
            response = requests.get(f"{base_url}/api/trading/opportunities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                new_total = data.get('total_count', 0)
                print(f"   - Opportunities after scheduler scan: {new_total}")
        else:
            print(f"   ❌ Scheduler trigger failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Force opportunity test completed!")

if __name__ == "__main__":
    test_force_opportunities()