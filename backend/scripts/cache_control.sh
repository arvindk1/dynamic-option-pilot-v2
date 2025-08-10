#!/bin/bash
# Cache Control Script - Manage cached data mode

BACKEND_DIR="/home/arvindk/devl/dynamic-option-pilot-v2/backend"
cd "$BACKEND_DIR"

case "$1" in
    "dump")
        echo "🚀 Creating market data dump..."
        python scripts/market_data_dump.py
        ;;
    "enable")
        echo "📁 Enabling cached data mode..."
        export USE_CACHED_DATA=true
        echo "✅ Set USE_CACHED_DATA=true"
        echo "🔄 Restart backend to apply changes:"
        echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        ;;
    "disable")
        echo "🔴 Disabling cached data mode (live API)..."
        export USE_CACHED_DATA=false
        echo "✅ Set USE_CACHED_DATA=false"
        echo "🔄 Restart backend to apply changes:"
        echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        ;;
    "status")
        echo "📊 Cache Status:"
        if [ -d "cache/market_data/$(date +%Y-%m-%d)" ]; then
            echo "✅ Today's cache exists: $(date +%Y-%m-%d)"
            echo "📁 Quotes: $(cat cache/market_data/$(date +%Y-%m-%d)/quotes.json 2>/dev/null | jq 'length' 2>/dev/null || echo '0') symbols"
            echo "⚡ Options: $(cat cache/market_data/$(date +%Y-%m-%d)/options.json 2>/dev/null | jq 'length' 2>/dev/null || echo '0') symbols"
        else
            echo "❌ No cache for today: $(date +%Y-%m-%d)"
        fi
        
        echo ""
        echo "🔧 Environment:"
        echo "   USE_CACHED_DATA=${USE_CACHED_DATA:-'false'}"
        ;;
    "setup")
        echo "🎯 Quick Setup for Rate Limit Avoidance:"
        echo ""
        echo "1️⃣ Creating data dump..."
        python scripts/market_data_dump.py
        echo ""
        echo "2️⃣ Enabling cached mode..."
        echo "export USE_CACHED_DATA=true" >> ~/.bashrc
        echo "✅ Added to ~/.bashrc"
        echo "" 
        echo "3️⃣ Restart your terminal or run:"
        echo "   source ~/.bashrc"
        echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        ;;
    *)
        echo "📁 Cache Control Script"
        echo ""
        echo "Usage: $0 {dump|enable|disable|status|setup}"
        echo ""
        echo "Commands:"
        echo "  dump     - Create fresh market data dump"
        echo "  enable   - Switch to cached data mode (avoid rate limits)"
        echo "  disable  - Switch to live API mode (real-time data)"
        echo "  status   - Show cache status and current mode"
        echo "  setup    - Complete setup for rate limit avoidance"
        echo ""
        echo "Examples:"
        echo "  $0 setup     # Complete setup"
        echo "  $0 dump      # Refresh data"
        echo "  $0 enable    # Avoid rate limits"
        echo "  $0 disable   # Use live data"
        ;;
esac