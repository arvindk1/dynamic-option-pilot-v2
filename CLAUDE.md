# CLAUDE.md - Dynamic Options Pilot v2 Session Guide

## 📖 ESSENTIAL CONTEXT - READ FIRST

**IMPORTANT**: Before starting any work, always read the comprehensive project overview:
- **Primary Reference**: `README.md` - Complete v2.0 architecture, migration plan, and development guidelines
- **Project Location**: `/home/arvindk/devl/dynamic-option-pilot-v2/README.md`
- **Key Sections**: Architecture overview, V1→V2 migration strategy, strategy system, external configuration
- **Troubleshooting Guide**: `TROUBLESHOOTING_GUIDE.md` - Latest fixes and debugging procedures for V2 architecture

The README contains the definitive project plan, architecture decisions, and development standards that must be followed.

### 🚀 SESSION START CHECKLIST (Updated 2025-08-03)
1. **Read README.md** - Current architecture and migration status
2. **Check TROUBLESHOOTING_GUIDE.md** - Latest fixes and debugging procedures
3. **✅ COMPLETED**: V1→V2 strategy migration (13 strategies loaded)
4. **✅ COMPLETED**: Externalized configuration system retrofit
5. **✅ COMPLETED**: Strategy Sandbox implementation (strategy-specific scans working)
6. **✅ COMPLETED**: Zero opportunities fix - Trading tab now shows 21+ opportunities
7. **Verify system status** - `curl http://localhost:8000/health`
8. **Review recent changes** - Git status and recent commits
9. **Check opportunities working** - `curl -s http://localhost:8000/api/trading/opportunities | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'Total: {data[\"total_count\"]}')"`
10. **Test sandbox functionality** - `curl -X POST http://localhost:8000/api/sandbox/test/run/{config_id}`

### 🔧 V2 DEBUGGING APPROACH
When encountering issues, follow the V2 debugging methodology:
1. **Check Browser Console First** - Identifies exact failing components and API endpoints
2. **Use TROUBLESHOOTING_GUIDE.md** - Reference for common issues and solutions
3. **Test API Endpoints Directly** - Use curl to isolate frontend vs backend issues
4. **Fix Backend APIs First** - Add missing endpoints before frontend changes
5. **Verify TypeScript Interfaces** - Ensure backend responses match frontend expectations

See `TROUBLESHOOTING_GUIDE.md` for complete debugging procedures and recent fixes.

## 🔒 FILE PROTECTION POLICY

**PROTECTED AREAS - NEVER MODIFY WITHOUT EXPLICIT USER PERMISSION:**

### Core System Files (PROTECTED)
- `backend/models/` - Database models and schemas
- `backend/core/` - Core orchestration and system logic  
- `backend/main.py` - FastAPI application entry point
- `src/main.tsx` - React application entry point
- `package.json` - Dependencies and build configuration
- `requirements.txt` - Python dependencies
- `.env` files - Environment configuration

### Infrastructure Files (PROTECTED)
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container build instructions
- `.github/` - CI/CD workflows
- Database migration files
- Authentication/security modules

### STRATEGY WORK ALLOWED AREAS:
- `backend/plugins/trading/` - Strategy implementations
- `backend/config/strategies/` - Strategy configurations
- `src/components/StrategiesTab.tsx` - Strategy UI components
- `backend/services/sandbox_service.py` - Strategy testing service
- `backend/api/sandbox.py` - Strategy testing API
- Strategy-related documentation files

### SAFETY PROTOCOL:
1. **Always ask before modifying protected files**
2. **Focus changes only on strategy-related components**
3. **Use git branches for experimental changes**
4. **Test changes in sandbox environment first**

## 🎯 CORE ARCHITECTURAL PRINCIPLES

### V1 to V2 Migration Philosophy
**V1 Location**: `/home/arvindk/devl/dynamic-option-pilot` (reference implementation)
**V2 Location**: `/home/arvindk/devl/dynamic-option-pilot-v2` (new extensible architecture)

**Guiding Principles**:
1. **Retain ALL V1 Functionality** - Every strategy, feature, and capability from V1 must be preserved
2. **Extensible Architecture** - Move from hardcoded implementations to plugin-based system
3. **NO Hardcoded Data** - All configuration, symbols, parameters must be externalized
4. **NO Mock Data** - All data should come from real sources or configurable generators
5. **Data Externalization** - Configuration files, universe lists, strategy parameters all external

## 🚨 CRITICAL: ZERO MOCK DATA POLICY (ENFORCED)

**ABSOLUTELY NO MOCK DATA OR FALLBACKS ANYWHERE IN THE SYSTEM**

This is a **MISSION CRITICAL** trading platform. Mock data and fallbacks cause confusion and mask critical system failures.

### ✅ HARDENED IMPLEMENTATION (2025-08-02):
- **✅ All Hardcoded Fallbacks REMOVED**: No more `["SPY", "QQQ", "IWM"]` fallbacks
- **✅ Explicit Runtime Errors**: `RuntimeError` thrown when universe files fail to load
- **✅ Critical Error Logging**: All failures logged to database with `HIGH` severity
- **✅ 501 Not Implemented**: Stubbed endpoints return proper HTTP status codes
- **✅ No Fallback Prices**: Market data failures throw `RuntimeError` instead of using cached values

### 🛡️ HARDENED ENFORCEMENT RULES:
1. **All data elements MUST point to external sources**:
   - YFinance API for market data (NO fallback prices)
   - Real broker APIs for account data  
   - Database for cached/historical data
   - Configuration files for parameters (NO hardcoded symbols)

2. **When data is unavailable, SYSTEM FAILS EXPLICITLY**:
   - `RuntimeError` with detailed error messages
   - Critical errors logged to database for monitoring
   - HTTP 501 for unimplemented features
   - System health dashboard shows real failures

### 🚫 NEVER ALLOWED:
- Hardcoded prices, percentages, or market values
- Demo/mock fallback data in production code
- Random data generation for missing APIs
- Placeholder values that could be mistaken for real data

**Remember**: It's better to show NO DATA than WRONG DATA in a trading system.

## 🧪 STRATEGY SANDBOX SYSTEM (✅ COMPLETED)

**Status**: The Strategy Sandbox is now **fully operational** with strategy-specific parameter templates and scanning logic.

**For Complete Implementation Details**: See `STRATEGY_SANDBOX_IMPLEMENTATION_SUMMARY.md`

### Quick API Reference:
```bash
# Test sandbox functionality
curl -X POST http://localhost:8000/api/sandbox/test/run/{config_id} \
  -H "Content-Type: application/json" \
  -d '{"max_opportunities": 3, "symbols": ["SPY", "QQQ"]}'

# Get parameter template
curl http://localhost:8000/api/sandbox/strategies/{strategy_id}/template

# Create strategy configuration
curl -X POST http://localhost:8000/api/sandbox/strategies/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "IRON_CONDOR", "name": "My Test", "config_data": {...}}'
```

## 🆕 ADDING NEW STRATEGIES TO V2

**For Complete Guide**: See `ADDING_NEW_STRATEGIES.md`

### Quick Steps:
1. Create JSON strategy configuration file in `backend/config/strategies/rules/`
2. Restart backend - Strategy automatically loaded
3. Test: `curl -X POST http://localhost:8000/api/strategies/YourNewStrategy/quick-scan`

**Automatic Features (No Code Required)**:
- ✅ Individual strategy scan endpoints
- ✅ Strategy-specific opportunity generation  
- ✅ Timeout protection (15s/30s)
- ✅ Performance metrics tracking
- ✅ Frontend integration
- ✅ Caching and database storage

## 🛠️ ESSENTIAL API TESTING COMMANDS

### System Health & Status
```bash
curl http://localhost:8000/health
curl http://localhost:8000/system/status
curl http://localhost:8000/plugins
```

### Core Trading Operations
```bash
# Trading opportunities
curl http://localhost:8000/api/trading/opportunities
curl -X POST http://localhost:8000/api/scheduler/scan/high_probability

# Strategy operations
curl http://localhost:8000/api/strategies/                    # List all strategies
curl -X POST http://localhost:8000/api/strategies/ThetaCropWeekly/quick-scan
```

### Frontend Proxy Testing
```bash
curl http://localhost:5173/api/trading/opportunities         # Should work via Vite proxy
curl http://localhost:5173/api/strategies/                   # Should work via Vite proxy
```

**For Complete API Reference**: See `TROUBLESHOOTING_GUIDE.md` - Database commands, cache inspection, and detailed testing procedures.

## 🎯 V2 SYSTEM STATUS (Updated 2025-08-03)

**✅ CORE FUNCTIONALITY COMPLETE:**
1. ✅ V1→V2 strategy migration (13 strategies loaded)
2. ✅ Externalized strategy configurations
3. ✅ JSON-first configuration system
4. ✅ Universe file loading system
5. ✅ Individual strategy scans working
6. ✅ Strategy Sandbox implementation (strategy-specific scans)
7. ✅ Parameter template system (dynamic UI forms)
8. ✅ Universe configuration fallback system

**🛡️ SECURITY & ARCHITECTURE HARDENING COMPLETE:**
- **✅ NO FALLBACKS POLICY**: All hardcoded fallbacks removed, explicit errors only
- **✅ FastAPI Dependency Injection**: Modern service architecture implemented
- **✅ 501 Not Implemented**: All stubbed endpoints return proper HTTP status codes
- **✅ Configuration Mappers**: Business logic separated from API routing
- **✅ Error Sanitization**: Production-safe error handling with sensitive data removal
- **✅ Consistent Response Models**: Type-safe API responses with Pydantic models

**🔒 PRODUCTION-READY SECURITY:**
- **Error Sanitization**: ✅ IMPLEMENTED - No sensitive data leakage
- **Explicit Failures**: ✅ IMPLEMENTED - System fails fast and loud
- **Critical Error Logging**: ✅ IMPLEMENTED - All failures logged to database
- **Dependency Injection**: ✅ IMPLEMENTED - Clean, testable architecture
- **Type Safety**: ✅ IMPLEMENTED - Consistent API contracts

**🧪 STRATEGY SANDBOX COMPLETE:**
- **Parameter Templates**: ✅ IMPLEMENTED - Dynamic UI forms for 70+ strategy parameters
- **Strategy-Specific Scanning**: ✅ IMPLEMENTED - Unique opportunity generation per strategy
- **Universe Configuration**: ✅ IMPLEMENTED - Robust fallback system for all scenarios
- **Performance Metrics**: ✅ IMPLEMENTED - Automatic calculation of win rates and risk-reward
- **End-to-End Testing**: ✅ VALIDATED - 8+ strategies tested successfully
- **Error-Free Operation**: ✅ ACHIEVED - No more universe configuration failures

**🎊 MISSION ACCOMPLISHED**: The V2 architecture with Strategy Sandbox is production-ready with enterprise-grade security, reliability, and full strategy testing capabilities!

---

## 📚 REFERENCE DOCUMENTATION

For detailed information, consult these specialized guides:

- **`README.md`** - Complete project architecture and development guidelines
- **`TROUBLESHOOTING_GUIDE.md`** - Debugging procedures, error analysis, database commands
- **`STRATEGY_SANDBOX_IMPLEMENTATION_SUMMARY.md`** - Complete sandbox implementation details
- **`COMPREHENSIVE_TEST_RESULTS.md`** - Full system testing results and performance metrics
- **`ADDING_NEW_STRATEGIES.md`** - Step-by-step guide for adding new trading strategies

This CLAUDE.md file contains only session-critical information for optimal performance.