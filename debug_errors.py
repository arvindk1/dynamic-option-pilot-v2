#!/usr/bin/env python3
"""
Comprehensive Error Detection Script for Dynamic Options Pilot v2
Detects common issues that could cause frontend/backend errors
"""

import requests
import json
import subprocess
import sys
from pathlib import Path

def check_backend_health():
    """Check if backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend Health: HEALTHY")
            print(f"   Plugins loaded: {health_data.get('plugins', {}).get('total_plugins', 0)}")
            return True
        else:
            print(f"❌ Backend Health: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health: {str(e)}")
        return False

def check_frontend_accessibility():
    """Check if frontend is accessible"""
    try:
        response = requests.get("http://localhost:5173/", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: ACCESSIBLE")
            return True
        else:
            print(f"❌ Frontend: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend: {str(e)}")
        return False

def check_strategies_loading():
    """Check if strategies are loading correctly"""
    try:
        response = requests.get("http://localhost:8000/api/strategies/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('strategies', [])
            print(f"✅ Strategies Loading: {len(strategies)} strategies loaded")
            
            # Check for specific strategy types
            enabled = [s for s in strategies if s.get('enabled', True)]
            print(f"   Enabled strategies: {len(enabled)}")
            
            return len(strategies) > 0
        else:
            print(f"❌ Strategies Loading: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strategies Loading: {str(e)}")
        return False

def check_opportunities_generation():
    """Check if opportunities are being generated"""
    try:
        response = requests.get("http://localhost:8000/api/trading/opportunities", timeout=10)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"✅ Opportunities: {total} opportunities available")
            return total > 0
        else:
            print(f"❌ Opportunities: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Opportunities: {str(e)}")
        return False

def check_frontend_proxy():
    """Check if frontend can proxy to backend"""
    try:
        response = requests.get("http://localhost:5173/api/strategies/", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend Proxy: WORKING")
            return True
        else:
            print(f"❌ Frontend Proxy: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend Proxy: {str(e)}")
        return False

def check_typescript_errors():
    """Check for TypeScript compilation errors"""
    try:
        result = subprocess.run(['npx', 'tsc', '--noEmit'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ TypeScript: NO ERRORS")
            return True
        else:
            print("❌ TypeScript ERRORS:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ TypeScript Check: {str(e)}")
        return False

def check_database_integrity():
    """Check database integrity"""
    try:
        response = requests.get("http://localhost:8000/api/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            hit_rate = data.get('hit_rate', 0)
            print(f"✅ Database: Cache hit rate {hit_rate:.1%}")
            print(f"   Live scans: {stats.get('live_scans', 0)}")
            print(f"   Memory hits: {stats.get('memory_hits', 0)}")
            return True
        else:
            print(f"❌ Database: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database: {str(e)}")
        return False

def check_environment_config():
    """Check environment configuration"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            if "TRADING_ENVIRONMENT=development" in content:
                print("✅ Environment: development mode configured")
                return True
            else:
                print("❌ Environment: Missing or wrong TRADING_ENVIRONMENT")
                print("   Should be: TRADING_ENVIRONMENT=development")
                return False
    else:
        print("❌ Environment: .env file not found")
        return False

def check_port_conflicts():
    """Check for port conflicts"""
    try:
        # Check if multiple processes are using the same ports
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        backend_ports = [line for line in lines if ':8000' in line]
        frontend_ports = [line for line in lines if ':5173' in line or ':5174' in line]
        
        print(f"✅ Port Check: Backend ports: {len(backend_ports)}, Frontend ports: {len(frontend_ports)}")
        
        if len(backend_ports) > 1:
            print("⚠️  Warning: Multiple processes on port 8000")
        if len(frontend_ports) > 1:
            print("⚠️  Warning: Multiple processes on frontend ports")
            
        return True
    except Exception as e:
        print(f"❌ Port Check: {str(e)}")
        return False

def main():
    """Run comprehensive error detection"""
    print("🔍 Dynamic Options Pilot v2 - Error Detection")
    print("=" * 50)
    
    checks = [
        ("Environment Config", check_environment_config),
        ("Backend Health", check_backend_health),
        ("Frontend Access", check_frontend_accessibility),
        ("Strategies Loading", check_strategies_loading),
        ("Opportunities", check_opportunities_generation),
        ("Frontend Proxy", check_frontend_proxy),
        ("TypeScript", check_typescript_errors),
        ("Database", check_database_integrity),
        ("Port Conflicts", check_port_conflicts),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        results[name] = check_func()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 No errors detected! System appears healthy.")
    else:
        print("🚨 Issues detected. Check failed items above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)