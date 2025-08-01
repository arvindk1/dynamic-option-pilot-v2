# Strategy Configuration Architecture Guide

## 📋 Overview

This guide explains the unified strategy configuration system in Dynamic Options Pilot v2, addressing the Test → Live deployment pipeline and data externalization principles.

## 🏗️ Architectural Principles

### **Core Principles**
1. **Zero Hardcoded Data**: All configuration externalized to files
2. **Environment Isolation**: Clean separation between Test, Development, and Production
3. **Safe Deployment**: Automated validation, backup, and rollback capabilities
4. **Universe Externalization**: Symbol lists in external files, not configuration arrays

### **Configuration Philosophy**
- **Single Format**: JSON-only configurations (YAML deprecated)
- **External References**: All data referenced via file paths, not embedded
- **Environment-Aware**: Automatic environment detection and settings application
- **Validation First**: All deployments validated before promotion

## 📁 Directory Structure

```
backend/config/strategies/
├── production/              # Live trading environment
│   ├── ThetaCropWeekly.json # Production-ready configurations
│   ├── IronCondor.json      # Conservative limits, full universes
│   └── ...
├── development/            # Testing environment  
│   ├── ThetaCropWeekly.json # Test-friendly settings
│   └── ...                 # Smaller universes, relaxed limits
├── sandbox/                # User experimentation
│   └── ThetaCropWeekly.json # Flexible testing configurations
├── templates/              # Strategy templates
│   └── StrategyTemplate.json
└── backups/               # Automatic backups
    └── ThetaCropWeekly_production_20250801_143022.json
```

## ⚙️ Configuration Format

### **Unified JSON Structure**
```json
{
  "strategy_name": "ThetaCrop Weekly",
  "strategy_type": "THETA_HARVESTING",
  "description": "Weekly theta capture using iron condors",
  
  "universe": {
    "universe_file": "backend/data/universes/thetacrop_symbols.txt",
    "universe_name": "thetacrop",
    "max_symbols": 10,
    "symbol_selection": "top_by_volume",
    "min_volume": 1000000
  },
  
  "position_parameters": {
    "target_dte_range": [5, 6, 7, 8, 9, 10],
    "delta_target": 0.20,
    "max_positions": 5
  },
  
  "entry_signals": {
    "min_probability_profit": 0.65,
    "allow_bias": ["NEUTRAL"]
  },
  
  "educational_content": {
    "best_for": "Consistent income generation",
    "risk_level": "LOW-MEDIUM"
  }
}
```

### **Key Fields Explained**

#### **Universe Configuration** ✅ Externalized
```json
"universe": {
  "universe_file": "backend/data/universes/thetacrop_symbols.txt",  // ✅ External file reference
  "max_symbols": 10,                                                // ✅ Configurable limit  
  "symbol_selection": "top_by_volume"                               // ✅ Selection algorithm
}
```

**❌ Old Approach (Deprecated)**:
```json
"universe": {
  "primary_symbols": ["SPY", "QQQ", "IWM"]  // ❌ Hardcoded data
}
```

#### **Environment Metadata** (Auto-added)
```json
"environment": "production",
"deployed_at": "2025-08-01T14:30:22.123456"
```

## 🚀 Test → Live Deployment Workflow

### **1. List Current Strategies**
```bash
# View all environments
python scripts/deploy_strategy.py list

# View specific environment
python scripts/deploy_strategy.py list --environment production
```

### **2. Test Strategy in Development**
```bash
# Set development environment
python scripts/deploy_strategy.py set-env development

# Restart backend to use development configs
python main.py

# Test strategy
curl -X POST http://localhost:8000/api/strategies/ThetaCropWeekly/quick-scan
```

### **3. Promote to Production**
```bash
# Promote tested strategy
python scripts/deploy_strategy.py promote ThetaCropWeekly --from development --to production

# Switch to production environment
python scripts/deploy_strategy.py set-env production

# Restart backend for production
python main.py
```

### **4. Verification**
```bash
# Verify production deployment
curl http://localhost:8000/api/strategies/ThetaCropWeekly/opportunities

# Check strategy configuration
python scripts/deploy_strategy.py list --environment production
```

## 🌍 Environment Management

### **Environment Variables**
```bash
# backend/.env
TRADING_ENVIRONMENT=PRODUCTION  # DEVELOPMENT, PRODUCTION, SANDBOX
```

### **Environment-Specific Settings**

#### **Production Environment**
- **Conservative Limits**: `max_positions: 10`, `max_symbols: 15`
- **Full Universes**: Complete symbol lists for maximum opportunities
- **Strict Validation**: All configurations validated before deployment
- **Automatic Backups**: Created before any changes

#### **Development Environment**  
- **Relaxed Limits**: `max_positions: 5`, `max_symbols: 10`
- **Smaller Universes**: Faster testing with reduced symbol sets
- **Flexible Validation**: Allows experimental configurations
- **Rapid Iteration**: Quick deployment for testing

#### **Sandbox Environment**
- **User Control**: Full parameter customization
- **Isolated Testing**: No impact on live or development systems
- **Experimental Features**: Test new strategies safely

## 📊 Universe Management System

### **Universe Files Structure**
```
backend/data/universes/
├── thetacrop_symbols.txt    # 13 liquid ETFs (expanded from 3)
├── mag7.txt                 # 7 tech giants  
├── top20.txt                # 20 most liquid stocks
├── etfs.txt                 # 18 sector ETFs
└── sector_leaders.txt       # 28 sector leaders
```

### **Universe File Format**
```text
# ThetaCrop Weekly Strategy Universe
# High-volume, liquid ETFs suitable for weekly iron condor trading

# Core ETFs (Primary targets)
SPY   # S&P 500 ETF - Primary target
QQQ   # Nasdaq-100 ETF - High options volume  
IWM   # Russell 2000 ETF - Good volatility

# Additional Liquid ETFs
TLT   # 20+ Year Treasury Bond ETF
GLD   # Gold ETF - Commodity exposure
XLF   # Financial Select Sector SPDR
...
```

### **Symbol Limitation Resolution**
- **Before**: Hardcoded 3 symbols (`["SPY", "QQQ", "IWM"]`)
- **After**: External file with 13 symbols + configurable `max_symbols: 10`
- **Result**: Strategies can now access up to 10 symbols from a pool of 13

## 🔧 Deployment Script Usage

### **Basic Commands**
```bash
# List all strategies across environments
python scripts/deploy_strategy.py list

# List production strategies only
python scripts/deploy_strategy.py list --environment production

# Promote strategy from development to production
python scripts/deploy_strategy.py promote ThetaCropWeekly \
  --from development --to production

# Set active environment
python scripts/deploy_strategy.py set-env production
```

### **Advanced Usage**
```bash
# Validate configuration before promotion
python scripts/deploy_strategy.py validate ThetaCropWeekly --environment development

# Rollback to previous version (via backup)
cp backend/config/backups/ThetaCropWeekly_production_20250801_143022.json \
   backend/config/strategies/production/ThetaCropWeekly.json

# View deployment history
ls -la backend/config/backups/ | grep ThetaCropWeekly
```

## 🛡️ Safety Features

### **Automatic Validation**
- **JSON Syntax**: Validates JSON structure
- **Required Fields**: Ensures all mandatory fields present
- **Universe Files**: Verifies external file references exist
- **Range Checks**: Validates numerical parameters

### **Backup System**
- **Pre-Deployment**: Automatic backup before any promotion
- **Timestamped**: Unique backup names with date/time
- **Easy Rollback**: Simple copy operation to restore
- **Retention**: Configurable backup retention policy

### **Environment Isolation**
- **Configuration Separation**: Each environment has isolated configs
- **Resource Limits**: Environment-appropriate position/symbol limits
- **Data Isolation**: No cross-contamination between environments

## 📚 Migration from Legacy System

### **Deprecated Components**
- ❌ **YAML Configurations**: Moved to `.deprecated/` directory
- ❌ **Hardcoded Symbols**: Replaced with universe file references
- ❌ **Dual Format System**: Unified on JSON only
- ❌ **rules/ Directory**: Moved to `production/` and `development/`

### **Migration Steps**
1. **Update Universe References**: Change `primary_symbols` to `universe_file`
2. **Move Configurations**: Relocate to appropriate environment directories
3. **Test Deployment**: Use deployment script to validate and promote
4. **Update Documentation**: Ensure all references point to new system

## 🎯 Best Practices

### **Configuration Management**
- ✅ **External References**: Use `universe_file` instead of `primary_symbols`
- ✅ **Environment Awareness**: Set appropriate limits per environment
- ✅ **Documentation**: Comment configuration choices clearly
- ✅ **Validation**: Test configurations before promotion

### **Deployment Workflow**
- ✅ **Test First**: Always test in development before production
- ✅ **Validate**: Use deployment script validation features
- ✅ **Backup**: Automatic backups protect against errors
- ✅ **Monitor**: Verify deployment success after promotion

### **Universe Management**
- ✅ **Liquid Symbols**: Choose high-volume, liquid options
- ✅ **Reasonable Limits**: Set `max_symbols` based on strategy needs
- ✅ **Regular Updates**: Review and update universe files periodically
- ✅ **Documentation**: Comment each symbol's purpose

## 🚨 Troubleshooting

### **Common Issues**

#### **"Strategy not found in environment"**
```bash
# Check if strategy exists
python scripts/deploy_strategy.py list --environment development

# If missing, copy from another environment
cp backend/config/strategies/production/ThetaCropWeekly.json \
   backend/config/strategies/development/
```

#### **"Universe file not found"**
```bash
# Verify universe file exists
ls -la backend/data/universes/thetacrop_symbols.txt

# Check configuration reference
grep -n "universe_file" backend/config/strategies/production/ThetaCropWeekly.json
```

#### **"Still seeing 3 symbols limit"**
- Restart backend after universe file updates
- Check `max_symbols` setting in strategy configuration
- Verify universe file contains more than 3 symbols

#### **"Environment changes not taking effect"**
```bash
# Verify environment variable
cat backend/.env | grep TRADING_ENVIRONMENT

# Restart backend
python main.py
```

## 📞 Support

### **Validation Commands**
```bash
# Test configuration validity
python -c "import json; json.load(open('backend/config/strategies/production/ThetaCropWeekly.json'))"

# Test universe file loading
python -c "with open('backend/data/universes/thetacrop_symbols.txt') as f: print([line.split()[0] for line in f if line.strip() and not line.startswith('#')])"

# Test environment detection
python -c "import os; print(f'Environment: {os.getenv(\"TRADING_ENVIRONMENT\", \"DEVELOPMENT\")}')"
```

### **Log Monitoring**
```bash
# Monitor deployment activity
tail -f backend/logs/backend.log | grep -E "(strategy|environment|universe)"

# Check for configuration errors
grep -E "(ERROR|WARN)" backend/logs/backend.log | grep -i config
```

---

**Last Updated**: 2025-08-01  
**Version**: v2.0  
**Status**: Production Ready ✅  
**Next Review**: 2025-09-01