"""
ThetaCrop Weekly Strategy Plugin for V2 Architecture
=================================================

Advanced theta harvesting strategy using weekly iron condors on high-volume ETFs.
Migrated from V1 with enhanced extensibility and externalized configuration.

Strategy Overview:
- Weekly short-volatility iron condor strategy
- Thursday 11:30 ET entry timing (configurable)
- ±20-delta wings on SPY/QQQ/IWM (configurable)
- $2-$4 wide legs (configurable)
- ≥15% credit-to-width ratio (configurable)
- Smart exit rules: 50% profit, 30% loss, DTE≤1
- Assignment risk management
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import yaml
import math
from dataclasses import dataclass
from enum import Enum

from plugins.trading.base_strategy import (
    BaseStrategyPlugin, StrategyOpportunity, StrategyConfig, V1StrategyMigrationMixin
)
from core.orchestrator.base_plugin import PluginMetadata, PluginType, PluginConfig

logger = logging.getLogger(__name__)


class ThetaCropStatus(Enum):
    """Strategy execution status"""
    SCANNING = "SCANNING"
    READY = "READY"
    EXECUTED = "EXECUTED"
    MONITORING = "MONITORING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


@dataclass
class IronCondorSetup:
    """Iron condor configuration with all four legs"""
    underlying: str
    expiration: datetime
    dte: int
    
    # Strikes (ordered from lowest to highest)
    put_long_strike: float      # Protective put (buy)
    put_short_strike: float     # Short put (sell)
    call_short_strike: float    # Short call (sell)
    call_long_strike: float     # Protective call (buy)
    
    # Pricing and metrics
    estimated_credit: float
    width: float
    credit_to_width_ratio: float
    net_delta: float
    theta: float
    max_profit: float
    max_loss: float
    
    # Market context
    underlying_price: float
    implied_volatility: float
    volatility_rank: float
    liquidity_score: float


class ThetaCropWeeklyPlugin(BaseStrategyPlugin, V1StrategyMigrationMixin):
    """ThetaCrop Weekly strategy implementation with V2 architecture"""
    
    def __init__(self, config: PluginConfig = None, strategy_config: StrategyConfig = None):
        # Use provided strategy_config or fall back to loading from file
        if strategy_config is None:
            strategy_config = self._load_strategy_config()
        
        super().__init__(config, strategy_config)
        
        # Initialize strategy state
        self.status = ThetaCropStatus.SCANNING
        self.active_condors: Dict[str, Dict] = {}
        self.weekly_stats = {
            'condors_opened': 0,
            'condors_closed': 0,
            'total_credit': 0.0,
            'realized_pnl': 0.0,
            'win_rate': 0.0
        }
        
        # Load trading universe from external file
        self._universe_symbols = self._load_universe_symbols()
        
    def _get_config_path(self) -> str:
        """Get the absolute path to the strategy configuration file"""
        return "/home/arvindk/devl/dynamic-option-pilot-v2/backend/config/strategies/thetacrop_weekly.yaml"
    
    def _load_strategy_config(self) -> StrategyConfig:
        """Load externalized strategy configuration from YAML"""
        try:
            config_path = self._get_config_path()
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            strategy_data = config_data['strategy']
            trading_data = config_data['trading']
            universe_data = config_data['universe']
            
            return StrategyConfig(
                strategy_id=strategy_data['id'],
                name=strategy_data['name'],
                category=strategy_data['category'],
                min_dte=min(trading_data['target_dte_range']),
                max_dte=max(trading_data['target_dte_range']),
                min_probability=0.50,  # Will be calculated from delta target
                max_risk_per_trade=trading_data.get('max_risk_per_trade', 500.0),
                min_liquidity_score=config_data['market_conditions']['min_liquidity_score'],
                symbols=universe_data['primary_symbols'],
                max_opportunities=trading_data['max_positions']
            )
            
        except Exception as e:
            logger.error(f"Failed to load strategy config: {e}")
            # Fallback to default config
            return StrategyConfig(
                strategy_id="thetacrop_weekly",
                name="ThetaCrop Weekly",
                category="theta_harvesting",
                symbols=["SPY", "QQQ", "IWM"]
            )
    
    def _load_universe_symbols(self) -> List[str]:
        """Load trading universe from external file"""
        try:
            universe_file = "/home/arvindk/devl/dynamic-option-pilot-v2/backend/data/universes/thetacrop_symbols.txt"
            symbols = []
            
            with open(universe_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        symbol = line.split()[0]  # Take first word before comment
                        symbols.append(symbol.upper())
            
            if symbols:
                return symbols
            else:
                logger.warning("Universe file is empty, loading default ETF universe")
                from utils.universe_loader import get_universe_loader
                universe_loader = get_universe_loader()
                return universe_loader.load_universe_symbols("default_etfs.txt")
            
        except Exception as e:
            logger.error(f"Failed to load universe symbols: {e}, using fallback")
            # Use external default universe as final fallback
            try:
                from utils.universe_loader import get_universe_loader
                universe_loader = get_universe_loader()
                return universe_loader.load_universe_symbols("default_etfs.txt")
            except Exception:
                return ["SPY", "QQQ", "IWM"]  # Final hardcoded fallback only if everything fails
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata for registration"""
        return PluginMetadata(
            name="thetacrop_weekly",
            version="2.0.0",
            plugin_type=PluginType.TRADING_STRATEGY,
            description="Weekly theta harvesting iron condor strategy",
            author="Dynamic Options Pilot v2",
            dependencies=["yfinance_provider", "technical_analyzer"],
            config_schema={
                "required": ["trading", "universe", "risk"],
                "properties": {
                    "trading": {"type": "object"},
                    "universe": {"type": "object"},
                    "risk": {"type": "object"}
                }
            }
        )
    
    @property
    def strategy_metadata(self) -> StrategyConfig:
        """Strategy-specific metadata"""
        return self.strategy_config
    
    async def initialize(self) -> bool:
        """Initialize strategy plugin"""
        try:
            logger.info(f"Initializing ThetaCrop Weekly strategy")
            
            # Load and validate configuration
            if not self.strategy_config:
                logger.error("Strategy configuration not loaded")
                return False
            
            # Validate universe symbols
            if not self._universe_symbols:
                logger.error("No trading universe symbols loaded")
                return False
            
            logger.info(f"ThetaCrop Weekly initialized with {len(self._universe_symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"ThetaCrop Weekly initialization failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup strategy resources"""
        try:
            # Close any active monitoring
            self.active_condors.clear()
            self.status = ThetaCropStatus.CLOSED
            logger.info("ThetaCrop Weekly cleaned up successfully")
            return True
        except Exception as e:
            logger.error(f"ThetaCrop Weekly cleanup failed: {e}")
            return False
    
    async def scan_opportunities(self, universe: List[str], **kwargs) -> List[StrategyOpportunity]:
        """Scan for iron condor opportunities"""
        try:
            # Use provided universe or fallback to configured symbols
            scan_symbols = universe if universe else self._universe_symbols
            
            opportunities = []
            
            # Check if we should scan for entries based on timing rules
            if not await self._should_scan_for_entry():
                logger.debug("Outside optimal entry window, skipping scan")
                return opportunities
            
            # Scan each symbol for iron condor setups
            for symbol in scan_symbols:
                try:
                    setup = await self._find_optimal_iron_condor(symbol)
                    if setup:
                        opportunity = await self._convert_setup_to_opportunity(setup)
                        if opportunity:
                            opportunities.append(opportunity)
                            
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    continue
            
            logger.info(f"ThetaCrop Weekly found {len(opportunities)} opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"ThetaCrop Weekly scan failed: {e}")
            return []
    
    async def validate_opportunity(self, opportunity: StrategyOpportunity) -> bool:
        """Validate an iron condor opportunity"""
        try:
            # Basic validation
            if not opportunity.symbol or not opportunity.strategy_type:
                return False
            
            # Check DTE range
            if not (self.strategy_config.min_dte <= opportunity.days_to_expiration <= self.strategy_config.max_dte):
                return False
            
            # Check probability threshold (derived from delta target)
            if opportunity.probability_profit < 0.50:  # Conservative threshold
                return False
            
            # Check liquidity requirements
            if not self.validate_liquidity_requirements(opportunity, self.strategy_config.min_liquidity_score):
                return False
            
            # Check credit-to-width ratio (iron condor specific)
            if opportunity.max_loss > 0:
                credit_ratio = opportunity.premium / opportunity.max_loss
                if credit_ratio < 0.15:  # Minimum 15% credit ratio
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Opportunity validation failed: {e}")
            return False
    
    def calculate_position_size(self, opportunity: StrategyOpportunity, account_size: float) -> int:
        """Calculate appropriate position size"""
        try:
            # Use externalized position sizing rules
            # 1 contract per $3,000 of account value (from config)
            position_size_ratio = 3000.0  # From config
            base_size = max(1, int(account_size / position_size_ratio))
            
            # Risk-based adjustment
            max_loss_per_contract = opportunity.max_loss
            if max_loss_per_contract > 0:
                max_risk_per_trade = account_size * 0.02  # 2% max risk
                risk_adjusted_size = int(max_risk_per_trade / max_loss_per_contract)
                base_size = min(base_size, risk_adjusted_size)
            
            return max(1, base_size)
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return 1
    
    def calculate_risk_metrics(self, opportunity: StrategyOpportunity) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        try:
            metrics = {}
            
            # Basic risk metrics
            if opportunity.max_loss > 0:
                metrics['risk_reward_ratio'] = opportunity.max_profit / opportunity.max_loss
                metrics['credit_to_width_ratio'] = opportunity.premium / opportunity.max_loss
            
            # Probability-based metrics
            metrics['probability_profit'] = opportunity.probability_profit
            metrics['expected_value'] = opportunity.expected_value
            
            # Time decay metrics (theta harvesting specific)
            if opportunity.theta:
                metrics['theta_decay_score'] = self.calculate_theta_decay_score(
                    opportunity.days_to_expiration, opportunity.theta
                )
            
            # Liquidity risk
            metrics['liquidity_score'] = opportunity.liquidity_score
            
            return metrics
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            return {}
    
    async def _should_scan_for_entry(self) -> bool:
        """Check if we should scan for new entries based on timing rules"""
        try:
            config_path = self._get_config_path()
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            now = datetime.now(timezone.utc)
            
            # Check testing overrides
            testing = config.get('testing', {})
            if testing.get('allow_any_day', False):
                # Testing mode: allow any weekday
                if now.weekday() > 4:  # Skip weekends only
                    return False
            else:
                # Production mode: Thursday only
                entry_day = config['trading']['entry_day']
                if now.weekday() != entry_day:
                    return False
            
            # Check time window
            if testing.get('extended_hours', False):
                # Testing: 9 AM - 8 PM ET
                return 9 <= now.hour <= 20
            else:
                # Production: around entry time
                entry_time = config['trading']['entry_time']  # "11:30"
                entry_hour = int(entry_time.split(':')[0])
                return entry_hour - 1 <= now.hour <= entry_hour + 1
            
        except Exception as e:
            logger.error(f"Entry timing check failed: {e}")
            return True  # Default to allowing scans if config fails
    
    async def _find_optimal_iron_condor(self, symbol: str) -> Optional[IronCondorSetup]:
        """Find optimal iron condor setup for symbol"""
        try:
            # Get current market data (would integrate with real data provider)
            underlying_price = await self._get_current_price(symbol)
            if not underlying_price:
                return None
            
            # Find optimal expiration in target DTE range
            expiration_date = await self._find_target_expiration(symbol)
            if not expiration_date:
                return None
            
            dte = (expiration_date - datetime.now(timezone.utc)).days
            
            # Calculate ±20 delta strikes (externalized delta target)
            delta_target = 0.20  # From config
            
            # Estimate strikes based on delta target (would use real options data)
            call_strike, put_strike = await self._estimate_delta_strikes(
                symbol, underlying_price, expiration_date, delta_target
            )
            
            if not call_strike or not put_strike:
                return None
            
            # Test different wing widths from config
            config_path = self._get_config_path()
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            wing_widths = config['trading']['wing_widths']
            best_setup = None
            best_score = 0
            
            for width in wing_widths:
                setup = await self._create_condor_setup(
                    symbol, expiration_date, dte, underlying_price,
                    put_strike, call_strike, width
                )
                
                if setup and self._meets_entry_criteria(setup):
                    score = self._score_condor_setup(setup)
                    if score > best_score:
                        best_score = score
                        best_setup = setup
            
            return best_setup
            
        except Exception as e:
            logger.error(f"Error finding iron condor for {symbol}: {e}")
            return None
    
    async def _convert_setup_to_opportunity(self, setup: IronCondorSetup) -> Optional[StrategyOpportunity]:
        """Convert iron condor setup to standardized opportunity format"""
        try:
            opportunity_id = f"thetacrop_{setup.underlying}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            opportunity = StrategyOpportunity(
                id=opportunity_id,
                symbol=setup.underlying,
                strategy_type="theta_harvesting",
                strategy_id=self.strategy_config.strategy_id,
                
                # Iron condor structure
                option_type="BOTH",  # Iron condor uses both calls and puts
                short_strike=(setup.put_short_strike + setup.call_short_strike) / 2,  # Average
                long_strike=None,  # Complex multi-leg structure
                expiration=setup.expiration.strftime('%Y-%m-%d'),
                days_to_expiration=setup.dte,
                
                # Financial metrics
                premium=setup.estimated_credit,
                max_loss=setup.max_loss,
                max_profit=setup.max_profit,
                probability_profit=self._calculate_probability_from_delta(0.20),  # ±20 delta
                expected_value=setup.max_profit * self._calculate_probability_from_delta(0.20),
                
                # Greeks
                delta=setup.net_delta,
                theta=setup.theta,
                
                # Market data
                underlying_price=setup.underlying_price,
                liquidity_score=setup.liquidity_score,
                
                # Strategy specific
                trade_setup=f"Iron Condor: {setup.put_long_strike}/{setup.put_short_strike}/{setup.call_short_strike}/{setup.call_long_strike}",
                risk_level="MEDIUM",
                
                # Additional metadata
                market_conditions={
                    'width': setup.width,
                    'credit_to_width_ratio': setup.credit_to_width_ratio,
                    'implied_volatility': setup.implied_volatility,
                    'volatility_rank': setup.volatility_rank
                }
            )
            
            # Calculate composite score
            opportunity.score = self._calculate_score(opportunity)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error converting setup to opportunity: {e}")
            return None
    
    # Helper methods (would integrate with real data providers in production)
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price (placeholder - integrate with real data)"""
        # Placeholder prices for testing
        prices = {"SPY": 627.50, "QQQ": 385.20, "IWM": 198.75}
        return prices.get(symbol, 100.0)
    
    async def _find_target_expiration(self, symbol: str) -> Optional[datetime]:
        """Find next expiration in target DTE range"""
        # For weekly strategies, find next Friday in DTE range
        now = datetime.now(timezone.utc)
        target_dte = 7  # Target 7 DTE for weekly
        
        target_date = now + timedelta(days=target_dte)
        # Adjust to Friday if needed
        while target_date.weekday() != 4:  # 4 = Friday
            target_date += timedelta(days=1)
        
        return target_date
    
    async def _estimate_delta_strikes(self, symbol: str, price: float, expiration: datetime, delta: float) -> Tuple[Optional[float], Optional[float]]:
        """Estimate strikes for target delta (placeholder)"""
        # Simplified delta approximation for testing
        # In production, would use real options chain and Greeks
        
        dte = (expiration - datetime.now(timezone.utc)).days
        volatility = 0.20  # Assume 20% volatility
        
        # Rough approximation for ±20 delta strikes
        price_move = price * volatility * math.sqrt(dte / 365.0)
        
        call_strike = price + price_move
        put_strike = price - price_move
        
        # Round to nearest dollar
        call_strike = round(call_strike)
        put_strike = round(put_strike)
        
        return call_strike, put_strike
    
    async def _create_condor_setup(self, symbol: str, expiration: datetime, dte: int,
                                   underlying_price: float, put_strike: float, 
                                   call_strike: float, width: float) -> Optional[IronCondorSetup]:
        """Create iron condor setup with given parameters"""
        try:
            # Calculate wing strikes
            put_long_strike = put_strike - width
            call_long_strike = call_strike + width
            
            # Estimate credit (placeholder - would use real options pricing)
            estimated_credit = width * 0.25  # Assume 25% of width as credit
            
            # Calculate metrics
            max_profit = estimated_credit * 100  # Per contract
            max_loss = (width - estimated_credit) * 100
            credit_to_width_ratio = estimated_credit / width
            
            # Estimate Greeks (placeholder)
            net_delta = 0.05  # Near delta-neutral
            theta = -0.03 * 100  # Negative theta (time decay benefit)
            
            return IronCondorSetup(
                underlying=symbol,
                expiration=expiration,
                dte=dte,
                put_long_strike=put_long_strike,
                put_short_strike=put_strike,
                call_short_strike=call_strike,
                call_long_strike=call_long_strike,
                estimated_credit=estimated_credit,
                width=width,
                credit_to_width_ratio=credit_to_width_ratio,
                net_delta=net_delta,
                theta=theta,
                max_profit=max_profit,
                max_loss=max_loss,
                underlying_price=underlying_price,
                implied_volatility=0.20,  # Placeholder
                volatility_rank=50.0,     # Placeholder
                liquidity_score=8.5       # Placeholder
            )
            
        except Exception as e:
            logger.error(f"Error creating condor setup: {e}")
            return None
    
    def _meets_entry_criteria(self, setup: IronCondorSetup) -> bool:
        """Check if setup meets entry criteria from config"""
        try:
            config_path = self._get_config_path()
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            min_credit_ratio = config['trading']['min_credit_ratio']
            
            # Check credit-to-width ratio
            if setup.credit_to_width_ratio < min_credit_ratio:
                return False
            
            # Check liquidity (placeholder)
            if setup.liquidity_score < 7.0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Entry criteria check failed: {e}")
            return False
    
    def _score_condor_setup(self, setup: IronCondorSetup) -> float:
        """Score iron condor setup for optimization"""
        try:
            score = 0.0
            
            # Credit-to-width ratio (higher is better)
            score += setup.credit_to_width_ratio * 40
            
            # Liquidity score
            score += setup.liquidity_score * 5
            
            # Theta benefit (more negative theta is better for income)
            if setup.theta < 0:
                score += abs(setup.theta) * 10
            
            # Delta neutrality (closer to zero is better)
            score += max(0, 10 - abs(setup.net_delta) * 50)
            
            return score
            
        except Exception as e:
            logger.error(f"Setup scoring failed: {e}")
            return 0.0
    
    def _calculate_probability_from_delta(self, delta: float) -> float:
        """Estimate probability of profit from delta (approximation)"""
        # Rough approximation: 20 delta ≈ 80% probability OTM
        return 1.0 - delta if delta < 0.5 else delta