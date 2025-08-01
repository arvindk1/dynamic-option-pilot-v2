# V1 Strategy Migration Plan
**Created**: 2025-07-30  
**Updated**: 2025-08-01
**Status**: Individual Strategy Scans Complete - Ready for Advanced Features

## ✅ COMPLETED: Individual Strategy Scans (2025-08-01)

**V1 had individual strategy scan endpoints like `/api/thetacrop/scan` - V2 now has this too!**

### What Was Implemented:
- ✅ **Individual Strategy Scan Endpoints**: All 13 V2 strategies now support individual scanning
- ✅ **V1 Compatibility**: Same functionality as V1's individual strategy scans
- ✅ **Externalized Configuration**: Uses JSON configs from `backend/config/strategies/rules/`
- ✅ **Timeout Protection**: 15s quick scans, 30s full scans (prevents hanging)
- ✅ **Real Universe Data**: Each strategy uses its configured `primary_symbols`

### New API Endpoints:
```bash
# Quick scans (15 second timeout)
POST /api/strategies/{strategy_id}/quick-scan

# Full scans (30 second timeout with detailed metrics)  
POST /api/strategies/{strategy_id}/scan

# Examples for all 13 strategies:
curl -X POST http://localhost:8000/api/strategies/ThetaCropWeekly/quick-scan
curl -X POST http://localhost:8000/api/strategies/IronCondor/scan
curl -X POST http://localhost:8000/api/strategies/RSICouponStrategy/quick-scan
```

### 13 Strategies Supporting Individual Scans:
1. ThetaCrop Weekly ✅    8. Calendar Spread ✅
2. Iron Condor ✅        9. Vertical Spread ✅  
3. RSI Coupon Strategy ✅ 10. Single Option ✅
4. Credit Spread ✅      11. Collar ✅
5. Protective Put ✅     12. Straddle ✅
6. Butterfly Spread ✅   13. Strangle ✅
7. Covered Call ✅

**V2 now matches V1's individual strategy scan capability with improved architecture!**

---

## 📊 V1 Strategy Audit

### V1 Strategies Found (11 strategies, 208 files total)
Based on the file list provided, here are the V1 strategies that need to be migrated:

| V1 Strategy | File Size | Complexity | Migration Priority | V2 Status |
|------------|-----------|------------|-------------------|-----------|
| `thetacrop_weekly.py` | 25,249 bytes | **HIGH** | **CRITICAL** | Missing |
| `thetacrop_plugin.py` | 14,802 bytes | **HIGH** | **CRITICAL** | Missing |
| `thetacrop_weekly_original.py` | 23,689 bytes | **HIGH** | Reference | Backup |
| `rsi_coupon_plugin.py` | 16,969 bytes | **MEDIUM** | **HIGH** | Missing |
| `iron_condor_plugin.py` | 13,703 bytes | **MEDIUM** | **MEDIUM** | Basic V2 exists |
| `credit_spread_plugin.py` | 13,786 bytes | **MEDIUM** | **MEDIUM** | Similar to V2 put_spread |
| `single_option_plugin.py` | 13,061 bytes | **LOW** | **LOW** | Missing |
| `volume_sentiment_plugin.py` | 10,819 bytes | **MEDIUM** | **MEDIUM** | Missing |
| `plugin_registry.py` | 11,592 bytes | **HIGH** | **CRITICAL** | V2 system different |
| `strategy_plugin.py` | 6,078 bytes | **HIGH** | **CRITICAL** | Missing base class |
| `__init__.py` | 1,151 bytes | **LOW** | **LOW** | Standard file |

### V1 vs V2 Gap Analysis

#### What V1 Had (Missing from V2):
1. **Sophisticated Plugin System**: Auto-discovery, registration, lifecycle management
2. **Advanced Theta Strategies**: Multiple theta decay harvesting approaches
3. **Technical Analysis Integration**: RSI-based opportunity detection  
4. **Sentiment Analysis**: Volume-based market sentiment
5. **Strategy Base Classes**: Common framework for all strategies
6. **Performance Tracking**: Strategy-specific metrics and optimization

#### What V2 Has (Advantages over V1):
1. **Modern Architecture**: FastAPI, async/await, better scalability
2. **Multi-layer Caching**: Memory + Database + Live scanning
3. **Real-time Updates**: WebSocket support for live data
4. **Better Error Handling**: Robust exception handling and logging
5. **Database Integration**: Persistent opportunity storage
6. **Plugin Infrastructure**: Base classes exist, ready for strategies

## 🎯 Migration Strategy

### Phase 4A: Critical Strategy Migration (Week 1)
**Goal**: Migrate the 3 most critical strategies first

#### 1. Theta Crop Weekly (CRITICAL - 25KB)
**Why Critical**: Likely the most popular and sophisticated strategy
**Migration Approach**:
```python
# Create: backend/plugins/trading/thetacrop_weekly_plugin.py
class ThetaCropWeeklyPlugin(BaseStrategyPlugin):
    def __init__(self):
        self.strategy_id = "thetacrop_weekly"
        self.name = "Theta Crop Weekly"
        self.category = "theta_harvesting"
        
    async def scan_opportunities(self, symbols: List[str]) -> List[Opportunity]:
        # Port V1 logic for weekly theta decay strategies
        # Focus on 0-7 DTE options with high theta decay
        pass
```

#### 2. RSI Coupon Plugin (HIGH - 17KB)  
**Why Critical**: Technical analysis integration
**Migration Approach**:
```python
# Create: backend/plugins/trading/rsi_coupon_plugin.py
class RSICouponPlugin(BaseStrategyPlugin):
    def __init__(self):
        self.strategy_id = "rsi_coupon"
        self.name = "RSI Coupon"
        self.category = "technical_analysis"
        
    async def scan_opportunities(self, symbols: List[str]) -> List[Opportunity]:
        # Port V1 RSI-based opportunity detection
        # Integrate with existing technical_analyzer plugin
        pass
```

#### 3. Strategy Plugin Base (CRITICAL - 6KB)
**Why Critical**: Foundation for all other strategies
**Migration Approach**:
```python
# Enhance: backend/plugins/trading/base_strategy.py
class BaseStrategyPlugin:
    # Port V1 common strategy functionality
    # Add performance tracking, risk management
    # Integrate with V2 plugin system
```

### Phase 4B: Medium Priority Migration (Week 2)

#### 4. Volume Sentiment Plugin (10KB)
**Migration Approach**: 
- Port volume analysis logic
- Integrate with market data providers
- Add sentiment scoring algorithms

#### 5. Enhanced Iron Condor (13KB)
**Migration Approach**:
- Enhance existing V2 iron_condor with V1 sophistication
- Add advanced selection criteria
- Improve risk management

#### 6. Credit Spread Enhancement (13KB)
**Migration Approach**:
- Enhance existing V2 put_spread with V1 credit_spread logic
- Add call spread variations
- Improve probability calculations

### Phase 4C: Completion & Testing (Week 3-4)

#### 7. Single Option Plugin (13KB)
**Migration Approach**:
- Add single-leg option strategies
- Implement calls, puts, and simple strategies

#### 8. Plugin Registry Enhancement (11KB)
**Migration Approach**:
- Enhance V2 plugin registry with V1 features
- Add auto-discovery and hot-reloading
- Improve strategy lifecycle management

## 🏗️ Technical Implementation Plan

### Step 1: Base Strategy Framework
```python
# backend/plugins/trading/base_strategy.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass 
class StrategyOpportunity:
    symbol: str
    strategy_type: str
    strikes: Dict[str, float]
    premium: float
    max_loss: float
    probability_profit: float
    days_to_expiration: int
    risk_metrics: Dict[str, Any]

class BaseStrategyPlugin(ABC):
    @abstractmethod
    async def scan_opportunities(self, symbols: List[str]) -> List[StrategyOpportunity]:
        pass
        
    @abstractmethod  
    def validate_opportunity(self, opportunity: StrategyOpportunity) -> bool:
        pass
        
    @abstractmethod
    def calculate_position_size(self, opportunity: StrategyOpportunity, account_size: float) -> int:
        pass
```

### Step 2: Strategy Registration System
```python
# backend/core/orchestrator/strategy_registry.py
class StrategyRegistry:
    def __init__(self):
        self.strategies: Dict[str, BaseStrategyPlugin] = {}
        
    def register_strategy(self, strategy: BaseStrategyPlugin):
        self.strategies[strategy.strategy_id] = strategy
        
    def get_all_strategies(self) -> List[BaseStrategyPlugin]:
        return list(self.strategies.values())
        
    def get_strategy(self, strategy_id: str) -> BaseStrategyPlugin:
        return self.strategies.get(strategy_id)
```

### Step 3: Strategy Integration with V2 Systems
```python
# Integrate with existing opportunity_cache.py
# Update main.py strategy endpoints to load from registry
# Add strategy performance tracking to database
```

## 📈 Migration Phases & Timeline

### Week 1: Foundation (Jan 1-7)
- ✅ Create BaseStrategyPlugin framework
- ✅ Enhance StrategyRegistry system  
- ✅ Migrate ThetaCropWeekly (most critical)
- ✅ Migrate RSICoupon (technical analysis)

### Week 2: Core Strategies (Jan 8-14)
- ✅ Migrate VolumeSentiment plugin
- ✅ Enhance IronCondor with V1 features
- ✅ Enhance CreditSpread capabilities
- ✅ Add strategy performance tracking

### Week 3: Completion (Jan 15-21)
- ✅ Migrate SingleOption plugin
- ✅ Complete plugin registry enhancements
- ✅ Add strategy configuration management
- ✅ Performance optimization

### Week 4: Testing & Polish (Jan 22-28)
- ✅ Integration testing with all strategies
- ✅ Performance benchmarking vs V1
- ✅ UI integration and testing
- ✅ Documentation and deployment

## 🎯 Success Metrics

### Immediate Success (Week 1):
- 3 critical strategies migrated and functional
- Strategy framework established
- Basic performance parity with V1

### Medium-term Success (Week 2-3):
- 6+ strategies migrated
- Enhanced features beyond V1 capabilities
- Strategy management UI working

### Final Success (Week 4):
- All 11 V1 strategies migrated
- Performance exceeds V1 
- Full feature parity + V2 enhancements

## 🔧 Development Workflow

### Migration Process for Each Strategy:
1. **Analysis**: Study V1 implementation
2. **Framework**: Create V2 plugin structure
3. **Core Logic**: Port opportunity scanning logic
4. **Integration**: Connect to V2 systems (cache, DB, API)
5. **Testing**: Unit tests and integration tests
6. **Optimization**: Performance tuning
7. **Documentation**: API docs and usage examples

### Quality Assurance:
- Unit tests for each strategy
- Integration tests with V2 systems
- Performance benchmarks vs V1
- UI testing with real data
- Backtesting with historical data

## 🚀 Next Steps

### Immediate Actions:
1. **Create BaseStrategyPlugin** in `backend/plugins/trading/`
2. **Enhance StrategyRegistry** in `backend/core/orchestrator/`
3. **Start with ThetaCropWeekly** migration (highest priority)

### Repository Structure:
```
backend/plugins/trading/
├── base_strategy.py           # Base strategy framework
├── thetacrop_weekly_plugin.py # Critical theta strategy
├── rsi_coupon_plugin.py       # Technical analysis strategy  
├── volume_sentiment_plugin.py # Market sentiment strategy
├── enhanced_iron_condor.py    # Enhanced volatility strategy
├── enhanced_credit_spread.py  # Enhanced credit strategy
└── single_option_plugin.py    # Simple option strategies
```

**Status**: Ready to begin implementation - V1 strategy migration framework designed and planned.