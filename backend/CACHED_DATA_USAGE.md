# 📁 Cached Data System - Rate Limit Avoidance

**Solution for Alpaca API rate limiting (429 errors) during development/testing.**

## 🚀 Quick Start

### Step 1: Create Data Dump
```bash
cd backend

# Run data dump script (one-time)
python scripts/market_data_dump.py

# Expected output:
# 🚀 Starting market data dump for 2025-08-04
# 📊 Dumping data for 27 symbols: ['SPY', 'QQQ', 'AAPL', ...]
# ✅ Data dump completed!
# 📁 Cache location: /backend/cache/market_data/2025-08-04/
```

### Step 2: Enable Cached Mode
```bash
# Set environment variable
export USE_CACHED_DATA=true

# Restart backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Look for this log message:
# 📁 Using cached data provider (rate limit avoidance mode)
# 📊 Quotes cache: 27 symbols
# ⚡ Options cache: 10 symbols
```

### Step 3: Verify No Rate Limits
```bash
# Test opportunities - should be FAST with no 429 errors
curl http://localhost:8000/api/trading/opportunities

# Should see all strategies working:
# ✅ JSON strategy Strangle found 2 opportunities  
# ✅ JSON strategy ThetaCrop Weekly found 10 opportunities
# ✅ All 13 strategies completing without timeouts
```

## 📋 Usage Modes

### Development Mode (Cached Data) 
```bash
export USE_CACHED_DATA=true
python -m uvicorn main:app --reload
```
**Pros**: ⚡ Fast, 🚫 No rate limits, 🔄 Consistent data  
**Cons**: 📅 Static data (refreshed daily)

### Production Mode (Live Data)
```bash
export USE_CACHED_DATA=false  # or unset
python -m uvicorn main:app --reload  
```
**Pros**: 📊 Real-time data, 📈 Live market prices  
**Cons**: ⏱️ Slower, 🚫 Rate limits possible

## 🔧 Technical Details

### Cache Structure
```
backend/cache/market_data/2025-08-04/
├── quotes.json      # Stock quotes for all symbols
└── options.json     # Options chains with Greeks
```

### Data Sources
- **Quotes**: All strategy symbols (SPY, QQQ, Top20, ThetaCrop universe)
- **Options**: Limited to 10 key symbols (to avoid rate limits during dump)
- **Greeks**: Generated from cached options data
- **Fallbacks**: Created for missing data

### Cache Behavior
1. **Cache Hit**: Use local data instantly ⚡
2. **Cache Miss**: Fallback to live Alpaca API ⚠️  
3. **API Failure**: Use generated fallback data 🔄

## 🎯 Problem Solved

**Before** (Rate Limited):
```
❌ 429 Client Error: Too Many Requests
❌ JSON strategy Strangle found 0 opportunities (timeout)
❌ Frontend shows 0 for most strategies
```

**After** (Cached):
```
✅ All strategies complete without timeouts
✅ Frontend shows correct opportunity counts
✅ No more rate limit errors
```

## 🔄 Daily Refresh

Run the data dump script daily to refresh cached data:

```bash
# Add to crontab for automatic daily refresh
0 8 * * * cd /path/to/backend && python scripts/market_data_dump.py
```

## 🏗️ Future Enhancements

1. **Intraday Updates**: Refresh cache every few hours
2. **Smart Caching**: Only cache symbols actually used by strategies  
3. **Database Backend**: Move from files to SQLite/PostgreSQL
4. **TTL Management**: Automatic expiration and refresh
5. **Selective Live Data**: Mix cached + live for specific symbols