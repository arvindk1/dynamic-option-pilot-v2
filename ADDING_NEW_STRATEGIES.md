# Adding New Strategies to Dynamic Options Pilot V2

## 🚀 Quick Start Guide

Adding a new strategy to V2 is designed to be as simple as creating a JSON configuration file. The system automatically handles all the infrastructure.

### Step 1: Create Strategy Configuration

Copy an existing strategy configuration as a template:

```bash
cd backend/config/strategies/rules/
cp IronCondor.json YourNewStrategy.json
```

### Step 2: Configure Your Strategy

Edit `YourNewStrategy.json` with your strategy parameters:

```json
{
  "module": "strategies.your_new_strategy",
  "strategy_name": "Your Strategy Name",
  "strategy_type": "YOUR_STRATEGY_TYPE",
  "description": "Brief description of what your strategy does",
  
  "universe": {
    "primary_symbols": ["SPY", "QQQ", "IWM", "AAPL", "MSFT"],
    "symbol_type": "ETF|LARGE_CAP_STOCK|ALL",
    "min_market_cap": 10000000000,
    "min_avg_volume": 5000000,
    "exclude_earnings": true
  },
  
  "position_parameters": {
    "min_dte": 21,
    "max_dte": 35,
    "max_opportunities": 5,
    "max_opportunities_per_symbol": 2
  },
  
  "entry_signals": {
    "allow_bias": ["NEUTRAL", "BULLISH", "BEARISH"],
    "required_bias": ["NEUTRAL"],
    "min_probability_profit": 0.65,
    "min_signal_strength": "MODERATE",
    "forbidden_volatility": ["HIGH"]
  },
  
  "scoring": {
    "base_probability_weight": 4.0,
    "premium_weight": 2.5,
    "score_ceiling": 10.0,
    "score_floor": 1.0,
    "round_decimals": 1
  },
  
  "risk_management": {
    "max_allocation_percentage": 25,
    "max_correlated_positions": 3,
    "max_portfolio_delta": 0.10
  },
  
  "educational_content": {
    "best_for": "Market conditions this strategy works best in",
    "when_to_use": "When to deploy this strategy",
    "profit_mechanism": "How the strategy makes money",
    "risk_level": "LOW|MEDIUM|HIGH",
    "typical_duration": "7-45 days",
    "max_profit": "Description of maximum profit potential",
    "max_loss": "Description of maximum loss potential"
  }
}
```

### Step 3: Restart Backend

The strategy will be automatically discovered and loaded:

```bash
cd backend
python main.py
```

Look for this log message:
```
Created and initialized strategy instance: YourNewStrategy
```

### Step 4: Test Your Strategy

Your strategy now automatically supports all V2 features:

```bash
# List all strategies (yours should appear)
curl http://localhost:8000/api/strategies/

# Test quick scan (15 second timeout)
curl -X POST http://localhost:8000/api/strategies/YourNewStrategy/quick-scan

# Test full scan (30 second timeout)
curl -X POST http://localhost:8000/api/strategies/YourNewStrategy/scan

# Get strategy-specific opportunities
curl http://localhost:8000/api/strategies/YourNewStrategy/opportunities
```

## 📋 Configuration Reference

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `strategy_name` | Display name in UI | `"Iron Condor"` |
| `strategy_type` | Category identifier | `"IRON_CONDOR"` |
| `description` | Brief strategy description | `"Market-neutral strategy..."` |
| `universe` | Symbol selection rules | `{"primary_symbols": ["SPY"]}` |
| `position_parameters` | DTE ranges, max opportunities | `{"min_dte": 21, "max_dte": 35}` |
| `entry_signals` | Market condition requirements | `{"allow_bias": ["NEUTRAL"]}` |
| `scoring` | Opportunity ranking rules | `{"base_probability_weight": 4.0}` |

### Optional Advanced Fields

| Field | Description | Default |
|-------|-------------|---------|
| `timing` | Entry timing rules | None |
| `strike_selection` | Strike selection logic | Auto-calculated |
| `exit_rules` | Exit condition rules | Basic profit/loss rules |
| `risk_management` | Portfolio risk controls | Conservative defaults |
| `adjustment_rules` | Position adjustment logic | None |

### Universe Configuration Options

```json
"universe": {
  // Primary symbols to scan
  "primary_symbols": ["SPY", "QQQ", "IWM"],
  
  // OR use preferred symbols
  "preferred_symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
  
  // Symbol filtering criteria
  "symbol_type": "ETF",              // ETF, LARGE_CAP_STOCK, ALL
  "min_market_cap": 10000000000,     // $10B minimum
  "min_avg_volume": 5000000,         // 5M daily volume
  "min_option_volume": 2000,         // 2000 option volume
  "exclude_earnings": true,          // Skip earnings announcements
  "exclude_earnings_days": 3         // Days before/after earnings
}
```

### Position Parameters

```json
"position_parameters": {
  "min_dte": 21,                    // Minimum days to expiration
  "max_dte": 35,                    // Maximum days to expiration
  "target_dte_range": [21, 28, 35], // Preferred DTE values
  "max_opportunities": 5,            // Max opportunities per scan
  "max_opportunities_per_symbol": 2, // Max per symbol
  "delta_target": 0.20,             // Target delta for strikes
  "position_size_per_3k": 1         // Position sizing rule
}
```

### Entry Signals

```json
"entry_signals": {
  "allow_bias": ["NEUTRAL", "BULLISH"],     // Allowed market bias
  "required_bias": ["NEUTRAL"],             // Required market bias
  "forbidden_volatility": ["HIGH"],         // Forbidden volatility regimes
  "min_probability_profit": 0.65,           // Minimum win probability
  "min_signal_strength": "MODERATE",        // WEAK, MODERATE, STRONG
  "min_credit_amount": 0.50,                // Minimum credit collected
  "max_net_delta_abs": 1.0,                 // Maximum net delta
  "volatility_requirements": {
    "iv_rank": {"min": 25, "max": 75},      // IV rank range
    "iv_percentile": {"min": 30, "max": 70} // IV percentile range
  }
}
```

### Scoring System

```json
"scoring": {
  "base_probability_weight": 4.0,      // Base probability multiplier
  "premium_weight": 2.5,               // Premium collection weight
  "ev_multiplier": 8.0,                // Expected value multiplier
  "signal_multiplier": {               // Signal strength bonuses
    "WEAK": 1.1,
    "MODERATE": 1.0,
    "STRONG": 0.85
  },
  "volatility_multiplier": {           // Volatility regime bonuses
    "LOW": 1.2,
    "NORMAL": 1.0,
    "HIGH": 0.8
  },
  "score_ceiling": 10.0,               // Maximum score
  "score_floor": 1.0,                  // Minimum score
  "round_decimals": 1                  // Score precision
}
```

## 🎯 Automatic Features

When you add a new strategy, you automatically get:

### ✅ Individual Strategy Scanning
- `POST /api/strategies/YourStrategy/quick-scan` - 15 second timeout
- `POST /api/strategies/YourStrategy/scan` - 30 second timeout with full metrics

### ✅ Strategy-Specific Opportunities
- `GET /api/strategies/YourStrategy/opportunities` - Get current opportunities

### ✅ Performance Tracking
- Scan counts, success rates, execution timing
- Opportunity generation statistics
- Error tracking and health monitoring

### ✅ Frontend Integration
- Automatic UI integration
- Strategy cards and filters
- Real-time opportunity display

### ✅ Caching & Database
- Multi-layer opportunity caching
- Database persistence
- Performance optimization

### ✅ Risk Management
- Portfolio allocation limits
- Correlation tracking
- Position sizing controls

### ✅ Timeout Protection
- Prevents system hangs
- Graceful error handling
- Performance monitoring

## 🔧 Advanced Customization

For strategies requiring custom logic beyond JSON configuration, create a custom plugin:

```python
# backend/plugins/trading/your_custom_strategy_plugin.py
from plugins.trading.json_strategy_plugin import JSONStrategyPlugin
from plugins.trading.base_strategy import StrategyOpportunity
from typing import List

class YourCustomStrategyPlugin(JSONStrategyPlugin):
    """Custom strategy with specialized opportunity generation logic."""
    
    async def _generate_opportunities(self, symbol: str, quote, data_provider, config) -> List[StrategyOpportunity]:
        """Override opportunity generation with custom logic."""
        opportunities = []
        
        # Your custom logic here
        # Access config: config.get('position_parameters', {})
        # Access market data: quote, data_provider
        # Generate opportunities based on your algorithm
        
        return opportunities
    
    def _calculate_custom_score(self, opportunity_data: dict) -> float:
        """Custom scoring algorithm."""
        # Implement your scoring logic
        return score
    
    async def _custom_universe_filter(self, symbols: List[str]) -> List[str]:
        """Custom symbol filtering logic."""
        # Filter symbols based on your criteria
        return filtered_symbols
```

Then register your custom plugin in the strategy registry or import it in `main.py`.

## 📊 Current V2 Strategies

All of these strategies support individual scanning:

1. **ThetaCrop Weekly** - `ThetaCropWeekly` - Theta decay harvesting
2. **Iron Condor** - `IronCondor` - Market-neutral range trading  
3. **RSI Coupon Strategy** - `RSICouponStrategy` - Mean reversion trades
4. **Credit Spread** - `CreditSpread` - Directional premium collection
5. **Protective Put** - `ProtectivePut` - Downside protection
6. **Butterfly Spread** - `Butterfly` - Low volatility profit
7. **Straddle** - `Straddle` - Long volatility play
8. **Strangle** - `Strangle` - Long volatility play
9. **Covered Call** - `CoveredCall` - Income generation
10. **Calendar Spread** - `CalendarSpread` - Time decay strategies
11. **Vertical Spread** - `VerticalSpread` - Directional trades
12. **Single Option** - `SingleOption` - Direct exposure
13. **Collar** - `Collar` - Protected positions

## 🚀 Testing Your Strategy

### Basic Functionality Test

```bash
# 1. Verify strategy is loaded
curl -s http://localhost:8000/api/strategies/ | grep "YourStrategy"

# 2. Test quick scan
curl -X POST http://localhost:8000/api/strategies/YourStrategy/quick-scan

# 3. Test full scan  
curl -X POST http://localhost:8000/api/strategies/YourStrategy/scan

# 4. Check opportunities
curl http://localhost:8000/api/strategies/YourStrategy/opportunities
```

### Performance Testing

```bash
# Monitor scan performance
curl -s http://localhost:8000/api/cache/stats | python3 -c "
import json,sys; data=json.load(sys.stdin); 
print(f'Live scans: {data[\"stats\"][\"live_scans\"]}')
print(f'Hit rate: {data[\"hit_rate\"]:.1%}')
"

# Check database storage
sqlite3 backend/dev.db "SELECT strategy_type, COUNT(*) FROM opportunity_snapshots GROUP BY strategy_type;"
```

### Health Monitoring

```bash
# Check strategy health
curl -s http://localhost:8000/api/strategies/YourStrategy/status

# Monitor logs
tail -f backend/logs/backend.log | grep "YourStrategy"
```

## 🎉 You're Done!

Your new strategy is now fully integrated into the V2 platform with all the infrastructure, APIs, caching, database persistence, and UI integration handled automatically. You can focus on the strategy logic while V2 handles everything else.

**Need help?** Check `CLAUDE.md` for troubleshooting or examine existing strategy configurations in `backend/config/strategies/rules/` for examples.