# Dynamic Option Pilot v2.0 - Quick Start Guide

## 🚀 Starting the Application

### Option 1: Start with Frontend in Background, Backend in Foreground
```bash
./scripts/start.sh
```
- ✅ **Frontend**: Runs in background
- ⚠️ **Backend**: Runs in foreground (you see logs, terminal is occupied)

### Option 2: Start Both in Background (Recommended for Development)
```bash
./scripts/start-detached.sh
```
- ✅ **Frontend**: Runs in background  
- ✅ **Backend**: Runs in background
- ✅ **Terminal**: Free to use for other commands
- 📝 **Logs**: Saved to `logs/frontend.log` and `backend/logs/backend.log`

### Option 3: Start in Separate Terminal Windows/Tabs
```bash
./scripts/start-separate.sh
```
- ✅ **Frontend**: Opens in new terminal window/tab
- ✅ **Backend**: Opens in new terminal window/tab
- ✅ **Visual**: Easy to see logs for each service

### Option 4: Start Backend and Frontend Separately

#### Start Backend Only:
```bash
cd backend
source venv/bin/activate
python main.py
```

#### Start Frontend Only:
```bash
./scripts/start-frontend.sh
```
Or manually:
```bash
# Make sure you're NOT in Python venv
deactivate  # if you were in one
npm run dev
```

## 🌐 Access Your Application

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173 (or 5174 if 5173 is busy)
- **Health Check**: http://localhost:8000/health

## 🔧 Common Commands

```bash
# Stop everything
./scripts/stop.sh

# Run tests
./scripts/test.sh

# Check system status
curl http://localhost:8000/system/status

# Get market data
curl http://localhost:8000/market-data/AAPL
```

## 🛠️ Troubleshooting

### Frontend Issues

**Problem**: `sh: 1: vite: not found`
**Solution**: Make sure you're not in Python virtual environment:
```bash
deactivate  # exit Python venv if you're in one
npm run dev
```

**Problem**: Port 5173 in use
**Solution**: Vite will automatically use port 5174 or another available port.

**Problem**: Dependencies not installed
**Solution**: 
```bash
npm install
```

### Backend Issues

**Problem**: Python virtual environment not found
**Solution**: 
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: Port 8000 in use
**Solution**:
```bash
./scripts/stop.sh  # Stop any running processes
./scripts/start.sh  # Restart
```

## 📊 Testing the API

### Quick Tests
```bash
# Health check
curl http://localhost:8000/health

# Get market data for Apple
curl http://localhost:8000/market-data/AAPL

# Get system status
curl http://localhost:8000/system/status

# Get plugin status
curl http://localhost:8000/plugins
```

### Using the API Documentation
Visit http://localhost:8000/docs to see interactive API documentation where you can test all endpoints.

## 🎯 What's Working

✅ **Backend**: FastAPI with plugin architecture  
✅ **Data Providers**: Yahoo Finance (primary), Alpaca (configured)  
✅ **Analysis**: Technical indicators (RSI, MACD, etc.)  
✅ **Frontend**: React with Vite and modern UI components  
✅ **Health Monitoring**: Real-time system status  
✅ **Configuration**: Environment-based settings  

## 🔄 Development Workflow

1. **Start the system**: `./scripts/start.sh`
2. **Make changes** to backend or frontend code
3. **Backend auto-reloads** on code changes
4. **Frontend auto-reloads** with hot module replacement
5. **Test your changes** via the frontend or API docs
6. **Run tests**: `./scripts/test.sh` (when ready)

## 📁 Key Files

- **Backend API**: `backend/main.py`
- **Plugin System**: `backend/core/orchestrator/`
- **Data Providers**: `backend/plugins/data/`
- **Analysis**: `backend/plugins/analysis/`
- **Frontend**: `src/` directory
- **Configuration**: `backend/config/environments/development.yaml`

## 📊 Important Database Tables

### 1. opportunity_snapshots
**Purpose**: Stores trading opportunity data with caching and expiration support

**Key Columns**:
- `id` (INTEGER, PK): Auto-incrementing primary key
- `opportunity_id` (VARCHAR, UNIQUE): Business identifier for the opportunity 
- `symbol` (VARCHAR, INDEXED): Stock symbol (AAPL, MSFT, etc.)
- `strategy_type` (VARCHAR, INDEXED): Trading strategy (high_probability, quick_scalp, swing_trade, etc.)
- `data` (JSON): Complete opportunity data including strikes, premiums, Greeks
- `created_at` (DATETIME, INDEXED): When opportunity was found
- `expires_at` (DATETIME, INDEXED): When opportunity expires from cache
- `scan_session_id` (VARCHAR, FK): Links to scan_sessions table
- `is_active` (BOOLEAN): Whether opportunity is still valid
- `cache_hits` (INTEGER): Number of times served from cache

**Performance Fields** (denormalized for fast filtering):
- `premium` (FLOAT): Option premium collected
- `max_loss` (FLOAT): Maximum potential loss
- `probability_profit` (FLOAT): Probability of profit (0.0-1.0)
- `expected_value` (FLOAT): Expected value of trade
- `days_to_expiration` (INTEGER): Days until options expire
- `underlying_price` (FLOAT): Current stock price
- `liquidity_score` (FLOAT): Options liquidity rating (0-10)

**Sample Data**:
```json
{
  "id": "scan_None_AAPL_1753925674",
  "symbol": "AAPL",
  "strategy_type": "high_probability", 
  "short_strike": 622,
  "long_strike": 616,
  "premium": 2.73,
  "max_loss": 730,
  "probability_profit": 0.776,
  "days_to_expiration": 32,
  "bias": "NEUTRAL",
  "rsi": 42
}
```

### 2. scan_sessions  
**Purpose**: Track scanning sessions and their results for debugging and analytics

**Key Columns**:
- `id` (VARCHAR, PK): Unique session identifier (UUID)
- `strategy` (VARCHAR, INDEXED): Strategy being scanned
- `symbols_scanned` (JSON): List of symbols that were scanned
- `started_at` (DATETIME): When scan began
- `completed_at` (DATETIME): When scan finished
- `opportunities_found` (INTEGER): Number of opportunities discovered
- `status` (VARCHAR): RUNNING, COMPLETED, FAILED, CANCELLED
- `error_message` (TEXT): Error details if scan failed
- `scan_parameters` (JSON): Configuration used for the scan

**Sample Data**:
```json
{
  "id": "uuid-scan-session-123",
  "strategy": "high_probability",
  "symbols_scanned": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
  "started_at": "2025-07-30T21:34:34",
  "completed_at": "2025-07-30T21:34:35", 
  "opportunities_found": 5,
  "status": "COMPLETED"
}
```

### Table Relationships
- `opportunity_snapshots.scan_session_id` → `scan_sessions.id`
- One scan session can produce multiple opportunities
- Opportunities expire and are cleaned up automatically
- Scan sessions provide audit trail and performance metrics

### Data Lifecycle
1. **Scanning**: New opportunities created during live scans
2. **Caching**: Opportunities cached in memory (2-15 min TTL) and database (15 min TTL)
3. **Serving**: Fast retrieval via memory → database → live scan fallback
4. **Expiration**: Automatic cleanup of expired opportunities
5. **Analytics**: Scan sessions track performance and errors

## 🎉 You're Ready!

Your Dynamic Option Pilot v2.0 is now running with:
- Modern plugin architecture
- Real-time market data
- Technical analysis
- Professional UI
- Comprehensive API
- Multi-layer caching system
- Opportunity tracking database

Happy trading! 🚀