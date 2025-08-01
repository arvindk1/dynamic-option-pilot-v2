#!/usr/bin/env python3
"""
Test opportunity generation through the running backend APIs.
"""

import requests
import json
import time

def test_api_opportunity_generation():
    """Test opportunity generation through API calls."""
    
    print("=== API Opportunity Generation Test ===\n")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Test backend health
    print("1. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Backend not responding: {e}")
        return
    
    # Step 2: Test strategies endpoint
    print("\n2. Testing strategies endpoint...")
    try:
        response = requests.get(f"{base_url}/api/strategies/", timeout=10)
        if response.status_code == 200:
            strategies = response.json()
            strategy_list = strategies.get('strategies', [])
            print(f"   ✅ {len(strategy_list)} strategies loaded")
            
            # Show first few strategies
            for i, strategy in enumerate(strategy_list[:5]):
                print(f"     {i+1}. {strategy['name']} ({strategy['id']}) - {strategy['total_opportunities']} opportunities")
        else:
            print(f"   ❌ Strategies endpoint failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error calling strategies endpoint: {e}")
        return
    
    # Step 3: Test individual strategy scans
    print("\n3. Testing individual strategy scans...")
    test_strategies = ['ThetaCropWeekly', 'IronCondor', 'RSICouponStrategy']
    
    for strategy_id in test_strategies:
        print(f"\n   Testing {strategy_id}:")
        try:
            # Try quick scan first
            response = requests.post(f"{base_url}/api/strategies/{strategy_id}/quick-scan", timeout=30)
            if response.status_code == 200:
                result = response.json()
                opportunities_found = result.get('opportunities_found', 0)
                scan_symbols = result.get('scan_symbols', [])
                success = result.get('success', False)
                
                print(f"     ✅ Quick scan successful: {opportunities_found} opportunities")
                print(f"     - Symbols scanned: {scan_symbols}")
                print(f"     - Success: {success}")
                
                # If no opportunities, try full scan
                if opportunities_found == 0:
                    print(f"     - Trying full scan...")
                    response = requests.post(f"{base_url}/api/strategies/{strategy_id}/scan", timeout=45)
                    if response.status_code == 200:
                        full_result = response.json()
                        full_opportunities = full_result.get('opportunities_found', 0)
                        print(f"     - Full scan result: {full_opportunities} opportunities")
                        
                        if 'opportunities' in full_result and full_result['opportunities']:
                            print(f"     - Sample opportunity details:")
                            opp = full_result['opportunities'][0]
                            print(f"       Symbol: {opp.get('symbol', 'N/A')}")
                            print(f"       Premium: ${opp.get('premium_collected', 0):.2f}")
                            print(f"       Max Loss: ${opp.get('max_loss', 0):.2f}")
                            print(f"       Probability: {opp.get('probability_of_profit', 0):.1%}")
                    else:
                        print(f"     ❌ Full scan failed: {response.status_code}")
            else:
                print(f"     ❌ Quick scan failed: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"     ❌ Error scanning {strategy_id}: {e}")
    
    # Step 4: Test trading opportunities endpoint
    print("\n4. Testing trading opportunities endpoint...")
    try:
        response = requests.get(f"{base_url}/api/trading/opportunities", timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunities', [])
            total_count = data.get('total_count', 0)
            cache_stats = data.get('cache_stats', {})
            
            print(f"   ✅ Trading opportunities endpoint working")
            print(f"   - Total opportunities: {total_count}")
            print(f"   - Cache stats: {cache_stats.get('stats', {})}")
            
            if opportunities:
                print(f"   - Sample opportunity:")
                opp = opportunities[0]
                print(f"     Symbol: {opp.get('symbol', 'N/A')}")
                print(f"     Strategy: {opp.get('strategy_type', 'N/A')}")
                print(f"     Premium: ${opp.get('premium', 0):.2f}")
        else:
            print(f"   ❌ Trading opportunities failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error calling trading opportunities: {e}")
    
    # Step 5: Test manual scan trigger
    print("\n5. Testing manual scan trigger...")
    try:
        response = requests.post(f"{base_url}/api/scheduler/scan/high_probability", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Manual scan triggered successfully")
            print(f"   - Result: {result}")
            
            # Wait and check for opportunities
            print("   - Waiting 5 seconds and checking for opportunities...")
            time.sleep(5)
            
            response = requests.get(f"{base_url}/api/trading/opportunities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                new_total = data.get('total_count', 0)
                print(f"   - Opportunities after scan: {new_total}")
        else:
            print(f"   ❌ Manual scan failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error triggering manual scan: {e}")
    
    print(f"\n✅ API test completed!")

if __name__ == "__main__":
    test_api_opportunity_generation()