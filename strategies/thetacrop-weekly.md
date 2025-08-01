# ThetaCrop Weekly Strategy

## Overview

The ThetaCrop Weekly strategy is an advanced theta harvesting approach that systematically sells weekly iron condors on high-volume ETFs to capture time decay premium. This strategy represents the flagship offering of the Dynamic Options Pilot v2 platform, migrated from V1 with enhanced extensibility and externalized configuration.

## Strategy Philosophy

**Core Thesis**: Time decay (theta) is the most predictable component of options pricing. By systematically selling time premium on liquid, broad-market ETFs with defined risk, we can generate consistent income while maintaining controlled risk exposure.

**Market Approach**: Short volatility with market-neutral positioning, benefiting from time decay while hedging directional risk through balanced wing structure.

## Technical Implementation

### Strategy Parameters (Externalized Configuration)

All strategy parameters are externalized in `backend/config/strategies/thetacrop_weekly.yaml`:

```yaml
trading:
  entry_day: 3  # Thursday (0=Monday)
  entry_time: "11:30"  # ET optimal entry time
  target_dte_range: [5, 6, 7, 8, 9, 10]  # Days to expiration
  delta_target: 0.20  # ±20 delta wings
  wing_widths: [2, 3, 4]  # $2-$4 spreads
  min_credit_ratio: 0.15  # Minimum 15% credit-to-width
  max_positions: 5  # Risk management limit
```

### Universe Selection (Externalized Data)

Trading universe defined in `backend/data/universes/thetacrop_symbols.txt`:
- **SPY** - S&P 500 ETF (primary target)
- **QQQ** - Nasdaq-100 ETF (high options volume)
- **IWM** - Russell 2000 ETF (volatility opportunities)

### Iron Condor Structure

```
Protective Call (Buy)     +20Δ Call Strike
    ↑
Short Call (Sell)        +20Δ Call Strike - Wing Width
    ↑
CURRENT PRICE            (Market Neutral Zone)
    ↓
Short Put (Sell)         -20Δ Put Strike + Wing Width  
    ↓
Protective Put (Buy)     -20Δ Put Strike
```

## Entry Criteria

### Timing Rules
- **Primary Entry**: Thursday 11:30 ET (optimal theta/gamma balance)
- **Testing Mode**: Configurable for any weekday during extended hours
- **Market Hours**: Regular trading hours preferred for optimal liquidity

### Setup Requirements
1. **Delta Target**: ±20 delta wings for balanced risk/reward
2. **Wing Width**: $2-$4 spreads (optimizes credit vs. risk)
3. **Credit Ratio**: Minimum 15% of wing width as premium collected
4. **DTE Range**: 5-10 days for optimal theta decay curve
5. **Liquidity**: Minimum 7.0 liquidity score for reliable execution

### Market Conditions Filter
```yaml
market_conditions:
  min_iv_rank: 20  # Minimum implied volatility rank
  max_iv_rank: 80  # Maximum implied volatility rank
  min_liquidity_score: 7.0  # Options liquidity requirement
  max_spread_width: 0.05  # Bid-ask spread limit
```

## Risk Management

### Position Sizing
- **Base Rule**: 1 iron condor per $3,000 account equity
- **Risk Adjustment**: Maximum 2% account risk per trade
- **Portfolio Limit**: Maximum 5 concurrent positions

### Exit Rules (Automated)
1. **Profit Target**: Close at 50% of maximum profit
2. **Stop Loss**: Close at 30% loss of premium collected
3. **Time Decay**: Close if 1 day or less to expiration
4. **Assignment Risk**: Close if underlying within 10% of short strikes

### Assignment Management
- **Early Assignment Detection**: Monitor in-the-money probability
- **Roll Strategy**: Consider rolling threatened side if time value remains
- **Exercise Management**: Automated handling of assignment scenarios

## Performance Metrics

### Target Performance
- **Win Rate**: 70-80% (high probability structure)
- **Average Return**: 15-25% per trade (on margin used)
- **Max Drawdown**: <5% (controlled risk profile)
- **Sharpe Ratio**: >1.5 (risk-adjusted returns)

### Key Performance Indicators
```python
performance:
  track_statistics: true
  log_trades: true
  calculate_sharpe: true
  benchmark_symbol: "SPY"
```

## Implementation Details

### Strategy Class Structure
```python
class ThetaCropWeeklyPlugin(BaseStrategyPlugin, V1StrategyMigrationMixin):
    """
    Advanced theta harvesting with externalized configuration
    """
    
    def scan_opportunities(self, universe: List[str]) -> List[StrategyOpportunity]:
        """Scan for optimal iron condor setups"""
        
    def validate_opportunity(self, opportunity: StrategyOpportunity) -> bool:
        """Validate setup against entry criteria"""
        
    def calculate_position_size(self, opportunity: StrategyOpportunity, account_size: float) -> int:
        """Risk-based position sizing"""
```

### Data Integration Points
1. **Market Data**: Real-time quotes, options chains, volatility metrics
2. **Technical Analysis**: IV rank, volatility regime detection
3. **Risk Metrics**: Greeks calculation, probability analysis
4. **Execution**: Order management, assignment monitoring

## Advanced Features

### Dynamic Adjustment
- **Volatility Regime Adaptation**: Adjust delta targets based on market conditions
- **Liquidity Optimization**: Real-time spread width monitoring
- **Risk Scaling**: Dynamic position sizing based on portfolio heat

### Machine Learning Integration
- **Setup Scoring**: Multi-factor opportunity ranking
- **Exit Timing**: Optimized profit-taking algorithms
- **Market Regime**: Automated strategy parameter adjustment

### Integration with V2 Architecture
```python
# Plugin Registration
strategy_registry.register_strategy_class(
    ThetaCropWeeklyPlugin,
    strategy_config
)

# Automated Scanning
opportunities = await strategy.scan_opportunities(universe_symbols)

# Risk Validation
valid_trades = [opp for opp in opportunities if strategy.validate_opportunity(opp)]
```

## Usage Examples

### Manual Strategy Execution
```python
# Initialize strategy
thetacrop = ThetaCropWeeklyPlugin()
await thetacrop.initialize()

# Scan for opportunities
opportunities = await thetacrop.scan_opportunities(["SPY", "QQQ", "IWM"])

# Validate and score
for opp in opportunities:
    if thetacrop.validate_opportunity(opp):
        risk_metrics = thetacrop.calculate_risk_metrics(opp)
        position_size = thetacrop.calculate_position_size(opp, account_size)
```

### Automated Execution
```python
# Register with scheduler for automated execution
scheduler.register_strategy(
    strategy_id="thetacrop_weekly",
    entry_schedule="Thursday 11:30 ET",
    monitoring_frequency="1 minute"
)
```

## Configuration Management

### Environment-Specific Settings
```yaml
# Development Configuration
testing:
  allow_any_day: true
  extended_hours: true
  mock_data_enabled: false

# Production Configuration  
production:
  strict_timing: true
  live_data_only: true
  risk_limits_enforced: true
```

### Universe Management
```bash
# Add new symbol to universe
echo "VTI   # Total Stock Market ETF" >> thetacrop_symbols.txt

# Update strategy configuration
vim backend/config/strategies/thetacrop_weekly.yaml
```

## Troubleshooting

### Common Issues
1. **No Opportunities Found**: Check market conditions, volatility environment
2. **Low Credit Ratios**: Adjust wing widths or delta targets
3. **Execution Issues**: Verify liquidity scores and spread widths

### Debug Commands
```bash
# Test strategy scanning
curl -X POST "http://localhost:8000/api/strategies/thetacrop_weekly/scan"

# Check strategy status
curl "http://localhost:8000/api/strategies/thetacrop_weekly/status"

# View configuration
cat backend/config/strategies/thetacrop_weekly.yaml
```

## Strategy Evolution

### V1 to V2 Migration Benefits
- **Externalized Configuration**: No hardcoded parameters
- **Enhanced Risk Management**: Sophisticated position sizing
- **Improved Execution**: Better liquidity handling
- **Advanced Analytics**: Comprehensive performance tracking

### Future Enhancements
- **Multi-Timeframe Analysis**: Incorporate daily and weekly signals
- **Volatility Surface Modeling**: Advanced options pricing
- **Portfolio Optimization**: Cross-strategy risk management
- **Alternative Assets**: Extension to other asset classes

---

*The ThetaCrop Weekly strategy represents the evolution of systematic options trading, combining proven theta harvesting principles with modern, extensible architecture for consistent income generation.*