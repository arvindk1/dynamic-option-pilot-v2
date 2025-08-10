# Dynamic Options Pilot v2 - Strategy Deployment Guide

## 🎯 Overview

This guide provides comprehensive instructions for deploying custom strategies from the Strategy Sandbox to live trading. The Dynamic Options Pilot v2 supports a complete workflow from strategy creation to production deployment.

## 🏗️ Architecture Overview

### 3-Tier Strategy System
```
📁 Base Strategies (13 templates)
├── /backend/config/strategies/development/ThetaCropWeekly.json
├── /backend/config/strategies/development/IronCondor.json
└── ... (11 more base strategies)

📁 Sandbox Configurations (Database)
├── SandboxStrategyConfig table
├── "ThetaCrop Weekly - Custom" (User's version)
├── "Protective Put - Custom" (User's version)
└── (Unlimited user configurations)

📁 Live Production Strategies  
├── /backend/config/strategies/production/MyCustomStrategy.json
└── (Deployed and actively trading)
```

### Data Flow
1. **Base Strategy** → Selected by user
2. **Sandbox Configuration** → Created with custom parameters
3. **Testing Phase** → Extensive backtesting and validation
4. **Deployment** → Promoted to production with safety checks
5. **Live Trading** → Generates real trading opportunities

## 🔄 Complete Deployment Workflow

### Phase 1: Strategy Creation & Customization

#### 1.1 Create Sandbox Strategy (UI Method)
1. Navigate to **Strategies** tab
2. Click **"New Strategy"** button
3. Select from 13 base strategies (ThetaCrop, Iron Condor, etc.)
4. Customize parameters:
   - **Universe**: Symbol selection (thetacrop, etfs, mag7)
   - **Trading Rules**: DTE ranges, position limits
   - **Risk Management**: Profit targets, loss limits
   - **Entry Signals**: RSI, volatility, bias filters

#### 1.2 Create Sandbox Strategy (API Method)
```bash
curl -X POST http://localhost:8000/api/sandbox/strategies/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "ThetaCropWeekly",
    "name": "My High-Performance ThetaCrop",
    "config_data": {
      "universe": {
        "universe_name": "thetacrop",
        "max_symbols": 8
      },
      "trading": {
        "target_dte_range": [14, 21],
        "max_positions": 3,
        "profit_target": 0.6,
        "loss_limit": -1.5
      },
      "risk": {
        "max_portfolio_risk": 0.02,
        "position_size_pct": 0.005
      },
      "entry_signals": {
        "rsi_oversold": 25,
        "volatility_max": 0.30,
        "bias": "NEUTRAL"
      }
    }
  }'
```

### Phase 2: Testing & Validation

#### 2.1 Run Comprehensive Tests
```bash
# Get your strategy config ID
CONFIG_ID=$(curl -s http://localhost:8000/api/sandbox/strategies/ | \
  python3 -c "import json,sys; data=json.load(sys.stdin); print(data[0]['id'])")

# Run multiple test scenarios
curl -X POST http://localhost:8000/api/sandbox/test/run/$CONFIG_ID \
  -H "Content-Type: application/json" \
  -d '{"max_opportunities": 20, "use_cached_data": true}'

# Test with different market conditions
curl -X POST http://localhost:8000/api/sandbox/test/run/$CONFIG_ID \
  -H "Content-Type: application/json" \
  -d '{"max_opportunities": 50, "use_cached_data": false}'
```

#### 2.2 Analyze Performance Metrics
Look for these key indicators before deployment:
- **Win Rate**: >60% (preferably >70%)
- **Expected Value**: Positive average return per trade
- **Risk/Reward Ratio**: >1.5 (reward should exceed risk)
- **Drawdown**: Maximum loss period <20%
- **Consistency**: Performance across different time periods

#### 2.3 Parameter Optimization
Fine-tune parameters based on test results:
```json
{
  "universe": {
    "max_symbols": 5,              // Reduce for focus
    "min_volume": 1000000          // Increase for liquidity
  },
  "trading": {
    "target_dte_range": [21, 30],  // Optimize timing
    "profit_target": 0.5,          // Adjust targets
    "loss_limit": -2.0
  },
  "entry_signals": {
    "rsi_oversold": 30,            // Fine-tune indicators
    "volatility_max": 0.25,        // Tighten filters
    "min_bias_strength": "STRONG"  // Require conviction
  }
}
```

### Phase 3: Pre-Deployment Validation

#### 3.1 Strategy Configuration Review
```bash
# Review your strategy configuration
curl http://localhost:8000/api/sandbox/strategies/$CONFIG_ID | python3 -m json.tool

# Verify universe files exist
ls -la backend/universe_lists/thetacrop.json

# Check for required fields
python3 -c "
import json, requests
config = requests.get('http://localhost:8000/api/sandbox/strategies/$CONFIG_ID').json()
required = ['universe', 'trading', 'risk', 'entry_signals']
missing = [f for f in required if f not in config['config_data']]
print('Missing fields:', missing if missing else 'None - Ready for deployment!')
"
```

#### 3.2 Risk Assessment
Calculate potential impact before going live:
```python
# Risk calculation example
portfolio_value = 100000  # Your portfolio size
max_risk_per_trade = 0.005  # 0.5% risk per position
max_positions = 3
total_max_risk = max_risk_per_trade * max_positions * portfolio_value
print(f"Maximum portfolio risk: ${total_max_risk}")  # Should be reasonable
```

### Phase 4: Deployment to Production

#### 4.1 CLI Deployment (Recommended Method)
```bash
cd backend/scripts/

# Step 1: List your sandbox strategies
python deploy_strategy.py list --environment sandbox

# Step 2: Validate strategy before promotion
python deploy_strategy.py promote "My High-Performance ThetaCrop" \
  --from sandbox --to production

# Expected output:
# 🚀 Promoting My High-Performance ThetaCrop: sandbox → production
# 💾 Created backup: backend/config/backups/MyStrategy_production_20250803_143022.json
# ✅ Successfully promoted My High-Performance ThetaCrop to production
```

#### 4.2 Set Production Environment
```bash
# Step 3: Activate production environment
python deploy_strategy.py set-env production

# Expected output:
# ✅ Environment set to: PRODUCTION
# ⚠️  Backend restart required for environment change to take effect

# Step 4: Restart backend to load new strategies
cd ../
python main.py
```

#### 4.3 Deployment Verification
```bash
# Verify strategy is loaded in production
curl http://localhost:8000/api/strategies/ | grep "My High-Performance ThetaCrop"

# Check deployment status
curl http://localhost:8000/api/sandbox/deploy/status/$CONFIG_ID

# Expected response:
{
  "config_id": "uuid-1234",
  "is_active": true,
  "deployed_at": "2025-08-03T14:30:22",
  "status": "deployed"
}
```

### Phase 5: Live Trading Monitoring

#### 5.1 Monitor Strategy Performance
```bash
# Check if strategy is generating opportunities
curl http://localhost:8000/api/trading/opportunities | \
  python3 -c "
import json,sys
data = json.load(sys.stdin)
my_strategy_ops = [op for op in data.get('opportunities', []) if 'My High-Performance ThetaCrop' in str(op)]
print(f'Opportunities from my strategy: {len(my_strategy_ops)}')
"

# Monitor specific strategy performance
curl "http://localhost:8000/api/strategies/My%20High-Performance%20ThetaCrop/opportunities"
```

#### 5.2 Live Trading Dashboard
1. Navigate to **Trading** tab in UI
2. Look for opportunities tagged with your strategy name
3. Monitor performance metrics in real-time
4. Track win/loss ratios and P&L

## 🛡️ Safety Features & Risk Management

### Automatic Production Safeguards
When promoting to production, the system automatically applies:

```json
{
  "position_parameters": {
    "max_positions": 10,           // Capped at 10 (vs unlimited sandbox)
    "max_opportunities": 15        // Limited opportunity generation
  },
  "universe": {
    "max_symbols": 15              // Symbol limit for performance
  },
  "risk": {
    "position_size_limit": 5000,   // Conservative position sizing
    "max_portfolio_risk": 0.02     // 2% maximum portfolio risk
  },
  "environment": "production",
  "deployed_at": "2025-08-03T14:30:22"
}
```

### Backup & Rollback System
```bash
# All deployments create automatic backups
ls -la backend/config/backups/
# MyStrategy_production_20250803_143022.json  <- Automatic backup

# Rollback if needed
cp backend/config/backups/MyStrategy_production_20250803_143022.json \
   backend/config/strategies/production/MyStrategy.json

# Restart backend to apply rollback
python backend/main.py
```

### Environment Isolation
- **Development**: Testing with relaxed limits
- **Sandbox**: User customization and testing
- **Production**: Live trading with conservative safeguards

## 🔧 Advanced Deployment Options

### Manual Deployment Process
For maximum control, you can deploy manually:

```bash
# 1. Export sandbox configuration  
curl http://localhost:8000/api/sandbox/strategies/$CONFIG_ID > my_strategy_config.json

# 2. Convert to production format
python3 -c "
import json
with open('my_strategy_config.json') as f:
    config = json.load(f)

# Extract and format for production
prod_config = {
    'strategy_name': config['name'],
    'strategy_type': 'CUSTOM_SANDBOX',
    'description': f'Deployed from sandbox: {config[\"name\"]}',
    **config['config_data'],
    'environment': 'production',
    'deployed_at': '2025-08-03T14:30:22'
}

with open('backend/config/strategies/production/MyCustomStrategy.json', 'w') as f:
    json.dump(prod_config, f, indent=2)
print('Manual deployment file created')
"

# 3. Validate and restart
python backend/scripts/deploy_strategy.py list --environment production
python backend/main.py
```

## 📊 Deployment Checklist

### Pre-Deployment
- [ ] Strategy tested extensively (>10 test runs)
- [ ] Win rate >60%
- [ ] Positive expected value
- [ ] Risk parameters validated
- [ ] Universe files exist and accessible
- [ ] Configuration JSON valid

### Deployment Process
- [ ] Backup created automatically
- [ ] Production limits applied
- [ ] Environment set to production
- [ ] Backend restarted successfully
- [ ] Strategy appears in `/api/strategies/`

### Post-Deployment
- [ ] Strategy generating opportunities
- [ ] Performance monitoring active
- [ ] Risk limits being enforced
- [ ] Can rollback if needed

## 🚨 Troubleshooting Common Issues

### Issue: "Strategy not found in sandbox"
```bash
# Check if strategy was created successfully
curl http://localhost:8000/api/sandbox/strategies/ | python3 -m json.tool

# Recreate if missing
curl -X POST http://localhost:8000/api/sandbox/strategies/ -d '{...}'
```

### Issue: "Validation failed - missing universe file"
```bash
# Check universe file exists
ls -la backend/universe_lists/thetacrop.json

# Fix path in configuration
curl -X PUT http://localhost:8000/api/sandbox/strategies/$CONFIG_ID \
  -d '{"config_data": {"universe": {"universe_name": "thetacrop"}}}'
```

### Issue: "Deployed strategy not generating opportunities"
```bash
# Check if strategy is loaded
curl http://localhost:8000/api/strategies/ | grep "My Strategy"

# Verify environment is production
grep TRADING_ENVIRONMENT backend/.env

# Check strategy scan logs
tail -f backend/logs/strategy_scan.log
```

## 📈 Success Metrics

Track these metrics for deployed strategies:
- **Total Opportunities**: Number generated per day/week
- **Win Rate**: Percentage of profitable trades
- **Average Return**: Expected value per opportunity
- **Sharpe Ratio**: Risk-adjusted performance
- **Maximum Drawdown**: Worst losing streak

## 🎯 Best Practices

1. **Start Small**: Deploy with conservative position sizes first
2. **Monitor Closely**: Watch performance for first week
3. **Document Changes**: Keep notes on parameter adjustments
4. **Regular Reviews**: Analyze performance monthly
5. **Risk Management**: Never risk more than 2% per position
6. **Diversification**: Don't put all capital in one strategy
7. **Continuous Testing**: Keep optimizing in sandbox

## 📞 Support & Resources

- **Troubleshooting**: See `TROUBLESHOOTING_GUIDE.md`
- **Architecture Details**: See `README.md`
- **Session Notes**: See `CLAUDE.md`
- **Protection System**: See `PROTECTION_SYSTEM.md`

**Remember**: Live trading involves real money and real risk. Always test thoroughly and start with small position sizes when deploying new strategies.