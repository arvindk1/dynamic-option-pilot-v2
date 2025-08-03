# 🚀 Dynamic Options Pilot v2 - Complete Platform Usage Guide

## 🎯 **What This Platform Does**

The Strategy Sandbox is your **powerful testing environment** for finding cheap option opportunities. You can:
- **Modify parameters** (DTE ranges, delta targets, wing widths) in real-time
- **Switch universes** instantly between MAG7, ETFs, Top20, ThetaCrop, Sector Leaders
- **Find cheap options** through sophisticated opportunity scoring
- **Test strategies** with batch parameter optimization
- **Deploy to live trading** when you're satisfied with results

## 🏁 **Quick Start - Your First Test**

### Step 1: Access the Strategy Sandbox
1. Open your browser to `http://localhost:5173`
2. Navigate to the **"Strategies"** tab
3. You'll see the Strategy Sandbox interface

### Step 2: Select or Create a Strategy
- **Left Sidebar**: Shows your existing strategy configurations
- **If empty**: Click "**Create Your First Strategy**" (or use existing ThetaCrop Weekly Test)
- **If strategies exist**: Click on one to select it

### Step 3: Run Your First Test
1. **Right Panel**: Click the green "**Run Test**" button
2. **Wait 5-15 seconds** for results
3. **View opportunities**: See individual opportunities with win rates, premiums, expected values

## 🎛️ **Advanced Platform Features**

### **🔧 Parameter Modification**

**To Change Parameters**:
1. In the strategy editor, find "**Strategy Parameters**" section
2. Click "**Edit Parameters**" button (toggles to edit mode)
3. **Modify values**:
   - **DTE Range**: Change from 7-28 to 14-45 (longer = more opportunities)
   - **Delta Target**: Adjust from 0.15 to 0.20 (risk/reward balance)
   - **Wing Widths**: Modify [5,10,15] to [10,20] (wider = more credit)
   - **Max Positions**: Change from 3 to 5 (more concurrent trades)
4. Click "**Save Changes**" (auto-saves in real-time)

**Real-time Preview**:
- Use `POST /api/sandbox/test/preview/{config_id}` for instant opportunity estimates
- See estimated impact before running full tests

### **🌍 Universe Management**

**Available Universes**:
- **MAG7**: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META (7 symbols)
- **ThetaCrop**: SPY, QQQ, IWM, TLT, GLD, XLF, XLE, XLK, XLV, XLI, EEM, VTI, ARKK (13 symbols)
- **ETFs**: 18 sector and broad market ETFs
- **Top20**: 20 most liquid large caps
- **Sector Leaders**: 28 leading stocks by sector

**To Change Universe**:
1. In edit mode, find "**Trading Universe**" section
2. Click the dropdown showing current universe
3. **Select new universe** (e.g., change from MAG7 to ThetaCrop)
4. **Preview symbols** before confirming
5. Universe automatically updates and saves

### **⚡ Batch Parameter Testing**

**Test Multiple Configurations Simultaneously**:

**API Endpoint**: `POST /api/sandbox/test/batch/{config_id}`

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/sandbox/test/batch/your-config-id \\
  -H "Content-Type: application/json" \\
  -d '{
    "parameter_sets": [
      {"trading.target_dte_range": [7, 21]},
      {"trading.target_dte_range": [21, 45]},
      {"trading.target_dte_range": [45, 60]}
    ]
  }'
```

**Results Include**:
- **Best performing parameter set** (highest expected value × win rate)
- **Individual results** for each parameter combination
- **Performance comparison** across all tests
- **Execution time** and opportunity counts

### **📊 A/B Comparison Testing**

**Compare Two Parameter Sets Head-to-Head**:

**API Endpoint**: `POST /api/sandbox/test/compare/{config_id}`

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/sandbox/test/compare/your-config-id \\
  -H "Content-Type: application/json" \\
  -d '{
    "parameter_set_a": {"trading.delta_target": 0.15},
    "parameter_set_b": {"trading.delta_target": 0.25},
    "test_name_a": "Conservative Delta",
    "test_name_b": "Aggressive Delta"
  }'
```

**Results Show**:
- **Winner determination** across multiple metrics
- **Performance differences** (opportunities, win rate, expected value)
- **Composite scoring** for overall best configuration

## 🤖 **AI Strategy Assistant**

### **Context-Aware Intelligence**

The AI Assistant **knows everything** about your current strategy:
- **Your parameters**: DTE ranges, delta targets, wing widths
- **Your universe**: Which symbols you're trading
- **Recent performance**: Win rates, expected values, opportunity counts
- **Market conditions**: When your strategy works best

### **How to Use the AI Assistant**

**Location**: Right panel in Strategy Sandbox

**Smart Greetings**:
- **Say "Hi"** → AI responds: *"I see you're working on ThetaCrop Weekly with SPY, QQQ, IWM targeting 7-28 DTE with 0.15 delta. Your recent test found 6 opportunities with 80.3% win rate. This strategy works well in neutral market conditions. What would you like to optimize?"*

**Optimization Questions**:
- *"How can I increase opportunities?"* → Suggests longer DTE ranges or larger universes
- *"What if I change to MAG7 universe?"* → Analyzes symbol liquidity and volume
- *"Should I adjust my delta target?"* → Explains risk/reward tradeoffs

**Market Condition Analysis**:
- *"When does this strategy work best?"* → Explains market regime suitability
- *"What's the optimal DTE for current conditions?"* → Strategic timing advice

### **AI Assistant API**

**Direct API Access**: `POST /api/sandbox/ai/chat/{config_id}`

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/sandbox/ai/chat/your-config-id \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "How can I find more cheap options?",
    "include_context": true
  }'
```

## 🔍 **Finding Cheap Options - The Core Workflow**

### **Method 1: Parameter Sweeping**
1. **Start with current parameters**
2. **Use batch testing** to try multiple DTE ranges:
   - Short-term: [7, 21] days
   - Medium-term: [21, 45] days  
   - Long-term: [45, 60] days
3. **Compare results** for opportunity count and premium levels
4. **Select best performing** parameter set

### **Method 2: Universe Optimization**
1. **Test current strategy** across different universes
2. **Compare ThetaCrop vs MAG7 vs ETFs**:
   - ThetaCrop: More symbols (13), better diversification
   - MAG7: Highest liquidity, tightest spreads
   - ETFs: Predictable behavior, good for beginners
3. **A/B compare** top 2 universes
4. **Deploy with winning universe**

### **Method 3: AI-Guided Optimization**
1. **Ask AI**: *"What changes would increase cheap option opportunities?"*
2. **Get specific suggestions**: DTE adjustments, delta targets, universe changes
3. **Implement suggestions** using parameter editing
4. **Test and validate** with batch testing
5. **Compare before/after** performance

## 🚀 **Deploying to Live Trading**

### **When You're Ready for Live Trading**

**Prerequisites**:
- ✅ Strategy tested thoroughly in sandbox
- ✅ Consistent opportunity generation (5+ opportunities per scan)
- ✅ Acceptable risk/reward metrics (>70% win rate, positive expected value)
- ✅ AI Assistant confirms strategy suitability

**Deployment Process**:
1. **Final validation**: Run multiple tests to ensure consistency
2. **Deploy**: `POST /api/sandbox/deploy/{config_id}`
3. **Monitor**: Strategy moves from "Testing" to "Live" status
4. **Track performance**: Live strategy will periodically scan for opportunities

**API Endpoint**:
```bash
curl -X POST http://localhost:8000/api/sandbox/deploy/your-config-id
```

**Response**:
```json
{
  "status": "success", 
  "message": "Strategy ThetaCrop Weekly deployed to live system",
  "deployed_at": "2025-08-02T18:35:00Z"
}
```

## 🛠️ **Advanced Features**

### **Error Monitoring & Health Dashboard**

**View Critical System Errors**:
- **Endpoint**: `GET /api/sandbox/errors/critical`
- **Dashboard**: `GET /api/sandbox/health/dashboard`

**Example Health Check**:
```bash
curl http://localhost:8000/api/sandbox/health/dashboard
```

**Response Shows**:
- **Overall system status**: HEALTHY/DEGRADED/DOWN
- **Critical errors in last 24h**: Count and details
- **Service health**: Individual component status
- **Error breakdown**: By type and resolution status

### **Performance Optimization**

**Real-time Opportunity Previews**:
```bash
curl -X POST http://localhost:8000/api/sandbox/test/preview/your-config-id \\
  -d '{"universe.primary_symbols": ["SPY", "QQQ", "IWM", "TLT"]}'
```

**Results**: Instant estimate of how changes affect opportunity count

**Historical Test Analysis**:
- **Endpoint**: `GET /api/sandbox/test/history/{config_id}`
- **View**: Past test performance, trends, optimization progress

## 📈 **Best Practices for Cheap Option Discovery**

### **1. Start Conservative, Optimize Gradually**
- **Begin with**: 7-28 DTE, 0.15 delta, proven universe (ThetaCrop)
- **Test thoroughly**: Run 5-10 tests to establish baseline
- **Optimize incrementally**: Change one parameter at a time

### **2. Use Data-Driven Decisions**  
- **Batch test** multiple scenarios before committing
- **A/B compare** final candidates head-to-head
- **Monitor metrics**: Prioritize expected value × win rate

### **3. Leverage AI Guidance**
- **Ask specific questions**: "How to increase opportunities without sacrificing quality?"
- **Get market insights**: "What DTE works best in current volatility regime?"
- **Validate strategies**: "Is this configuration optimal for neutral markets?"

### **4. Monitor System Health**
- **Check error dashboard** regularly for data issues
- **Validate universe loading** - ensure no hardcoded fallbacks
- **Review opportunity quality** - avoid artificially inflated numbers

## 🔧 **Troubleshooting Common Issues**

### **AI Assistant Not Responding**
- **Check**: OpenAI API key configuration in environment variables
- **Verify**: `curl -X POST /api/sandbox/ai/chat/test -d '{"message":"Hi"}'`
- **Solution**: API now uses modern OpenAI client (fixed in v2.1)

### **Wrong Universe Symbols**
- **Problem**: Seeing hardcoded AAPL, MSFT, GOOGL instead of universe file symbols
- **Check**: Universe file loading in `/backend/data/universes/`
- **Solution**: Fixed to use actual universe files, no more hardcoded fallbacks

### **Zero Opportunities**
- **Check**: Strategy scanning vs demo data fallbacks
- **Verify**: `curl /api/trading/opportunities` returns real data
- **Solution**: Demo data removed, shows true system state

### **Data Provider Issues**
- **Current**: yfinance (adequate for testing, 15-20 min delays)
- **Upgrade**: Polygon.io recommended for live trading ($199/month)
- **Professional**: TD Ameritrade or Interactive Brokers for execution

## 🎯 **Summary: Your Powerful Platform**

**You now have a sophisticated options trading sandbox that**:
- ✅ **Finds cheap options** through real opportunity scanning
- ✅ **Tests parameters** with batch optimization
- ✅ **Switches universes** instantly with real symbol loading
- ✅ **Provides AI guidance** with full strategy context
- ✅ **Deploys to live trading** when ready
- ✅ **Monitors system health** with error logging
- ✅ **Prevents data issues** with no hardcoded fallbacks

**Next Steps**:
1. **Test the platform** with your first strategy scan
2. **Experiment** with different parameters and universes
3. **Use AI assistance** for optimization guidance
4. **Deploy your best strategy** to live trading
5. **Monitor performance** and iterate

Your Strategy Sandbox is ready for serious options trading strategy development! 🚀