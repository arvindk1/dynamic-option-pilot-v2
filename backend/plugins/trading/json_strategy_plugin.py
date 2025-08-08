"""
JSON Strategy Plugin
===================
Generic strategy plugin that executes JSON-defined strategies.
Supports both Strategy Tab (testing) and Trading Tab (live execution).
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta, date
import asyncio
import random

from plugins.trading.base_strategy import BaseStrategyPlugin, StrategyOpportunity, StrategyConfig
from core.orchestrator.base_plugin import PluginConfig, PluginMetadata, PluginType
from core.strategies.json_strategy_loader import JSONStrategyConfig
from core.engines.engine_registry import EngineRegistry, EngineType
from core.interfaces.data_provider_interface import IDataProvider, DataProviderType

logger = logging.getLogger(__name__)


class JSONStrategyPlugin(BaseStrategyPlugin):
    """
    Generic strategy plugin that executes JSON-defined strategies.
    
    This plugin bridges the gap between JSON strategy configurations
    and the V2 plugin system, enabling both Strategy Tab testing 
    and Trading Tab live execution.
    """
    
    def __init__(self, 
                 config: PluginConfig, 
                 strategy_config: StrategyConfig,
                 json_config: JSONStrategyConfig, 
                 engine_registry: EngineRegistry):
        super().__init__(config, strategy_config)
        self.json_config = json_config
        self.engine_registry = engine_registry
    
    def _round_to_standard_strike(self, price: float) -> float:
        """Round price to standard option strike intervals"""
        if price < 5:
            # Round to nearest $0.50 for stocks under $5
            return round(price * 2) / 2
        elif price < 25:
            # Round to nearest $1.00 for stocks $5-$25
            return round(price)
        elif price < 200:
            # Round to nearest $2.50 for stocks $25-$200
            return round(price / 2.5) * 2.5
        else:
            # Round to nearest $5.00 for stocks over $200
            return round(price / 5) * 5
    
    def _calculate_proper_dte(self, target_dte: int) -> int:
        """Calculate proper days to expiration for options"""
        # Add some realistic variation around target DTE
        import random
        variation = random.randint(-3, 7)  # -3 to +7 days variation
        return max(1, target_dte + variation)
    
    def _calculate_expiration_date(self, target_dte: int) -> str:
        """Calculate realistic expiration date for options"""
        from datetime import datetime, timedelta
        
        actual_dte = self._calculate_proper_dte(target_dte)
        expiration_date = datetime.now() + timedelta(days=actual_dte)
        
        # Round to Friday (standard options expiration)
        days_ahead = expiration_date.weekday()
        if days_ahead < 4:  # Monday=0, Tuesday=1, ... Thursday=3
            days_to_friday = 4 - days_ahead
        else:  # Friday=4, Saturday=5, Sunday=6
            days_to_friday = (4 - days_ahead) % 7
        
        friday_expiration = expiration_date + timedelta(days=days_to_friday)
        return friday_expiration.strftime('%Y-%m-%d')
    
    def _calculate_delta(self, spot_price: float, strike_price: float, strategy_type: str, variant: int) -> float:
        """Calculate realistic delta for option positions"""
        if not strike_price:
            return 0.0
        
        # Simple delta approximation based on moneyness
        moneyness = spot_price / strike_price
        
        if strategy_type in ['PROTECTIVE_PUT']:
            # Protective puts are typically OTM puts with negative delta
            return round(-0.15 - variant * 0.03, 3)
        elif strategy_type in ['STRANGLE', 'STRADDLE']:
            # Net delta for strangles/straddles (close to neutral)
            return round(0.05 - variant * 0.02, 3)
        elif 'CALL' in strategy_type:
            # Call strategies have positive delta
            delta = 0.30 + (moneyness - 1) * 0.50
            return round(max(0.05, min(0.95, delta)), 3)
        else:
            # Default delta
            delta = 0.25 + (moneyness - 1) * 0.30
            return round(max(-0.95, min(0.95, delta)), 3)
    
    def _calculate_gamma(self, spot_price: float, strike_price: float, strategy_type: str) -> float:
        """Calculate realistic gamma for option positions"""
        if not strike_price:
            return 0.0
        
        # Gamma is highest ATM and decreases as we move away
        moneyness = abs(spot_price / strike_price - 1)
        max_gamma = 0.015
        
        # Gamma decreases exponentially as we move away from ATM
        gamma = max_gamma * (1 - moneyness * 3)
        return round(max(0.001, gamma), 4)
    
    def _calculate_theta(self, spot_price: float, strike_price: float, strategy_type: str, variant: int) -> float:
        """Calculate realistic theta (time decay) for option positions"""
        if not strike_price:
            return 0.0
        
        # Theta is typically negative (time decay hurts long positions)
        base_theta = -0.08 - variant * 0.02
        
        if strategy_type in ['PROTECTIVE_PUT']:
            # Long puts lose money to time decay
            return round(base_theta * 1.2, 3)
        elif strategy_type in ['STRANGLE', 'STRADDLE']:
            # Long straddles/strangles lose more to time decay
            return round(base_theta * 2.0, 3)
        else:
            return round(base_theta, 3)
    
    def _calculate_vega(self, spot_price: float, strike_price: float, strategy_type: str) -> float:
        """Calculate realistic vega for option positions"""
        if not strike_price:
            return 0.0
        
        # Vega is positive for long options, negative for short
        base_vega = 0.12
        
        if strategy_type in ['PROTECTIVE_PUT']:
            return round(base_vega * 0.8, 3)
        elif strategy_type in ['STRANGLE', 'STRADDLE']:
            # Long straddles/strangles benefit from volatility increases
            return round(base_vega * 1.5, 3)
        else:
            return round(base_vega, 3)
        self._performance_stats = {
            'total_scans': 0,
            'opportunities_generated': 0,
            'avg_scan_time': 0.0,
            'last_scan_time': None
        }
        
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name=f"json_strategy_{self.json_config.strategy_id}",
            version="2.0.0",
            plugin_type=PluginType.TRADING_STRATEGY,
            description=f"JSON Strategy: {self.json_config.description}",
            author="Dynamic Option Pilot - JSON Strategy System",
            dependencies=[]
        )
    
    @property
    def strategy_metadata(self) -> StrategyConfig:
        """Return strategy configuration metadata."""
        return self.strategy_config
    
    async def scan_opportunities(self, universe: List[str], **kwargs) -> List[StrategyOpportunity]:
        """
        Execute strategy scan based on JSON configuration.
        
        Args:
            universe: List of symbols to scan
            **kwargs: Additional parameters (e.g., provider_type for testing)
            
        Returns:
            List of StrategyOpportunity objects
        """
        scan_start_time = datetime.now()
        self._performance_stats['total_scans'] += 1
        
        try:
            # Get effective configuration (with overrides for Strategy Tab testing)
            effective_config = self.json_config.get_effective_config()
            
            # Get data provider (allow runtime override for testing)
            provider_type = kwargs.get('data_provider')
            if isinstance(provider_type, str):
                provider_type = DataProviderType(provider_type)
            
            data_provider = self.engine_registry.get_data_provider(provider_type)
            if not data_provider:
                logger.error(f"No data provider available for {self.json_config.strategy_id}")
                return []
            
            # Apply universe filtering from JSON config
            filtered_universe = await self._filter_universe(universe, data_provider, effective_config)
            
            # Scan each symbol using JSON-defined rules
            opportunities = []
            for symbol in filtered_universe:
                symbol_opportunities = await self._scan_symbol(symbol, data_provider, effective_config)
                opportunities.extend(symbol_opportunities)
            
            # Apply JSON-defined scoring and ranking
            scored_opportunities = self._apply_json_scoring(opportunities, effective_config)
            
            # Limit results per JSON config
            max_opps = effective_config.get('position_parameters', {}).get('max_opportunities', 10)
            final_opportunities = sorted(scored_opportunities, key=lambda x: x.score, reverse=True)[:max_opps]
            
            # Update performance stats
            scan_duration = (datetime.now() - scan_start_time).total_seconds()
            self._update_performance_stats(scan_duration, len(final_opportunities))
            
            logger.info(f"JSON strategy {self.json_config.strategy_id} found {len(final_opportunities)} opportunities")
            return final_opportunities
            
        except Exception as e:
            logger.error(f"Error scanning with JSON strategy {self.json_config.strategy_id}: {e}")
            return []
    
    async def _filter_universe(self, universe: List[str], data_provider: IDataProvider, config: Dict[str, Any]) -> List[str]:
        """Apply JSON-defined universe filtering."""
        universe_config = config.get('universe', {})
        
        # If no universe config, use provided universe
        if not universe_config:
            return universe
        
        filtered = []
        
        # Check for preferred symbols
        if 'preferred_symbols' in universe_config:
            preferred = universe_config['preferred_symbols']
            # Use preferred symbols if they're in the universe
            filtered = [s for s in preferred if s in universe]
            if filtered:
                logger.debug(f"Using preferred symbols: {filtered}")
                return filtered
        
        # Apply symbol type filtering
        symbol_types = universe_config.get('symbol_types', [])
        if symbol_types:
            # For now, assume all symbols are valid for the types
            # In a real implementation, you'd check symbol metadata
            filtered = universe.copy()
        else:
            filtered = universe.copy()
        
        # Apply volume/market cap filtering (would need real data)
        min_volume = universe_config.get('min_avg_volume', 0)
        if min_volume > 0:
            # For now, just log the requirement
            logger.debug(f"Filtering for min volume: {min_volume}")
        
        return filtered[:universe_config.get('max_universe_symbols', len(filtered))]
    
    async def _scan_symbol(self, symbol: str, data_provider: IDataProvider, config: Dict[str, Any]) -> List[StrategyOpportunity]:
        """Scan a single symbol using JSON-defined rules."""
        try:
            # Get market data
            quote = await data_provider.get_quote(symbol)
            
            # Apply entry signal filters
            if not await self._passes_entry_signals(symbol, quote, config):
                return []
            
            # Generate opportunities based on strategy type
            opportunities = await self._generate_opportunities(symbol, quote, data_provider, config)
            
            return opportunities
            
        except Exception as e:
            logger.warning(f"Error scanning {symbol}: {e}")
            return []
    
    async def _passes_entry_signals(self, symbol: str, quote, config: Dict[str, Any]) -> bool:
        """Check if symbol passes JSON-defined entry signals."""
        entry_signals = config.get('entry_signals', {})
        
        # Price range filtering
        if 'price_range' in entry_signals:
            price_range = entry_signals['price_range']
            min_price = price_range.get('min', 0)
            max_price = price_range.get('max', float('inf'))
            if not (min_price <= quote.price <= max_price):
                return False
        
        # Volume filtering
        if 'min_volume' in entry_signals:
            min_volume = entry_signals['min_volume']
            if quote.volume < min_volume:
                return False
        
        # Strategy-specific entry signals
        strategy_type = config.get('strategy_type', '').upper()
        
        if strategy_type == 'RSI_COUPON':
            # RSI-based filtering (simulated for now)
            rsi_threshold = entry_signals.get('rsi_below', 50)
            simulated_rsi = 30 + (hash(symbol) % 40)  # Simulated RSI between 30-70
            if simulated_rsi >= rsi_threshold:
                return False
        
        elif strategy_type in ['IRON_CONDOR', 'BUTTERFLY']:
            # Neutral bias requirement
            required_bias = entry_signals.get('required_bias', [])
            if required_bias and 'NEUTRAL' not in required_bias:
                return False
        
        elif strategy_type in ['STRADDLE', 'STRANGLE']:
            # High volatility requirement
            min_volatility = entry_signals.get('volatility_min', 0.0)
            simulated_iv = 0.2 + (hash(symbol) % 20) / 100  # Simulated IV between 0.2-0.4
            if simulated_iv < min_volatility:
                return False
        
        return True
    
    async def _generate_opportunities(self, symbol: str, quote, data_provider: IDataProvider, config: Dict[str, Any]) -> List[StrategyOpportunity]:
        """Generate strategy opportunities based on JSON configuration."""
        opportunities = []
        position_params = config.get('position_parameters', {})
        strategy_type = config.get('strategy_type', '').upper()
        
        # Determine number of opportunities to generate
        max_per_symbol = position_params.get('max_opportunities_per_symbol', 2)
        
        # Generate opportunities based on strategy type
        for i in range(min(max_per_symbol, 3)):  # Limit to 3 per symbol
            opportunity = await self._create_opportunity(symbol, quote, config, i, data_provider)
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _create_opportunity(self, symbol: str, quote, config: Dict[str, Any], variant: int = 0, data_provider: IDataProvider = None) -> Optional[StrategyOpportunity]:
        """Create a single opportunity based on JSON configuration."""
        try:
            position_params = config.get('position_parameters', {})
            strategy_type = config.get('strategy_type', 'UNKNOWN')
            
            # Generate realistic option parameters based on strategy type
            if strategy_type == 'IRON_CONDOR':
                delta_target = position_params.get('delta_target', 0.20)
                short_strike_call = self._round_to_standard_strike(quote.price * (1 + delta_target + variant * 0.02))
                short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta_target - variant * 0.02))
                wing_width = position_params.get('wing_widths', [5, 10])[variant % 2]
                
                premium = 2.0 + variant * 0.5
                max_loss = wing_width * 100 - premium * 100
                
            elif strategy_type in ['THETA_HARVESTING', 'COVERED_CALL']:
                # Theta harvesting strategies - sell options to collect premium
                delta_target = position_params.get('delta_target', 0.20)
                short_strike_call = self._round_to_standard_strike(quote.price * (1 + delta_target + variant * 0.02))
                short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta_target - variant * 0.02))
                
                premium = 1.8 + variant * 0.4
                max_loss = 500 + variant * 200
                
            elif strategy_type == 'RSI_COUPON':
                delta_range = position_params.get('preferred_delta_range', [0.25, 0.40])
                delta = delta_range[0] + (delta_range[1] - delta_range[0]) * variant / 2
                short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta))
                
                premium = 1.5 + variant * 0.3
                max_loss = 500 + variant * 100
                short_strike_call = None
                
            elif strategy_type in ['PUT_SPREAD', 'CREDIT_SPREAD', 'VERTICAL_SPREAD']:
                delta_targets = position_params.get('delta_targets', [0.10, 0.15, 0.20])
                delta = delta_targets[variant % len(delta_targets)]
                short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta))
                
                premium = 1.2 + variant * 0.4
                max_loss = 400 + variant * 150
                short_strike_call = None
                
            elif strategy_type in ['STRADDLE', 'STRANGLE']:
                # Volatility plays - buy both calls and puts
                atm_strike = quote.price
                short_strike_call = self._round_to_standard_strike(atm_strike * (1 + 0.05 * variant))
                short_strike_put = self._round_to_standard_strike(atm_strike * (1 - 0.05 * variant)) if strategy_type == 'STRANGLE' else self._round_to_standard_strike(atm_strike)
                
                premium = 3.5 + variant * 0.8  # Higher premium for volatility plays
                max_loss = premium * 100
                
            elif strategy_type == 'BUTTERFLY':
                # Butterfly spread - neutral strategy
                center_strike = quote.price
                wing_width = position_params.get('wing_widths', [10, 15])[variant % 2]
                short_strike_call = center_strike
                short_strike_put = center_strike
                
                premium = 1.0 + variant * 0.3
                max_loss = wing_width * 100 - premium * 100
                
            elif strategy_type == 'PROTECTIVE_PUT':
                # Protective put - insurance for long stock position
                # Long 100 shares + Long 1 Put for downside protection
                protection_level = position_params.get('protection_level', 0.95)  # 95% protection level
                long_strike_put = self._round_to_standard_strike(quote.price * protection_level)
                
                # Premium PAID for put protection (insurance cost)
                premium_paid = 2.5 + variant * 0.8  # Cost to buy protection
                
                # Max loss = stock decline to put strike + premium paid for protection
                max_loss = (quote.price - long_strike_put) * 100 + premium_paid * 100
                
                # Protective put has NO short option - only long stock + long put
                short_strike_call = None
                short_strike_put = None  # No short option in protective put
                
                # Store the long put strike for display
                premium = premium_paid  # Cost paid, not collected
                
            elif strategy_type in ['COLLAR', 'CALENDAR_SPREAD']:
                # Collar or calendar spread strategies
                delta_target = position_params.get('delta_target', 0.20)
                short_strike_call = self._round_to_standard_strike(quote.price * (1 + delta_target + variant * 0.02))
                short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta_target - variant * 0.02))
                
                premium = 1.3 + variant * 0.4
                max_loss = 400 + variant * 150
                
            elif strategy_type == 'NAKED_OPTION':
                # Single option play
                delta_target = position_params.get('delta_target', 0.30)
                # Randomly choose call or put
                if (hash(f"{symbol}_{variant}") % 2) == 0:
                    short_strike_call = self._round_to_standard_strike(quote.price * (1 + delta_target + variant * 0.02))
                    short_strike_put = None
                else:
                    short_strike_put = self._round_to_standard_strike(quote.price * (1 - delta_target - variant * 0.02))
                    short_strike_call = None
                
                premium = 2.5 + variant * 0.6
                max_loss = float('inf')  # Unlimited risk for naked options
                
            else:
                # Generic opportunity
                short_strike_put = self._round_to_standard_strike(quote.price * 0.85)
                premium = 2.0 + variant * 0.5
                max_loss = 600 + variant * 100
                short_strike_call = None
            
            # Calculate metrics
            probability_profit = 0.65 + (hash(f"{symbol}_{variant}") % 30) / 100  # 0.65-0.95
            expected_value = premium * 100 * probability_profit - max_loss * (1 - probability_profit)
            
            # Create opportunity
            # For Greeks calculation, use the appropriate strike based on strategy type
            if strategy_type == 'PROTECTIVE_PUT' and 'long_strike_put' in locals():
                greek_calculation_strike = long_strike_put
            else:
                greek_calculation_strike = short_strike_call or short_strike_put
            
            opportunity = StrategyOpportunity(
                id=f"json_{self.json_config.strategy_id}_{symbol}_{variant}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                strategy_type=strategy_type,
                strategy_id=self.json_config.strategy_id,
                universe=config.get('universe', {}).get('universe_name', 'default'),  # CRITICAL FIX: Add universe attribute
                underlying_price=quote.price,
                
                # Option details - handle Protective Put specially
                short_strike=long_strike_put if strategy_type == 'PROTECTIVE_PUT' and 'long_strike_put' in locals() else (short_strike_put if short_strike_put else short_strike_call),
                long_strike=long_strike_put if strategy_type == 'PROTECTIVE_PUT' and 'long_strike_put' in locals() else (
                    (short_strike_put - 10) if short_strike_put else ((short_strike_call + 10) if short_strike_call else None)
                ),
                
                # Financial metrics
                premium=premium,
                max_loss=max_loss,
                probability_profit=probability_profit,
                expected_value=expected_value,
                
                # Greeks (from real options data - will be populated by _get_real_options_data)
                delta=0.0,  # Will be updated with real data
                gamma=0.0,  # Will be updated with real data
                theta=0.0,  # Will be updated with real data
                vega=0.0,   # Will be updated with real data
                
                # Metadata - Use proper options expiration dates
                days_to_expiration=self._calculate_proper_dte(position_params.get('target_dtes', [30])[0]),
                expiration=self._calculate_expiration_date(position_params.get('target_dtes', [30])[0]),
                volume=quote.volume,
                open_interest=1000 + variant * 500,
                liquidity_score=8.0 + variant * 0.3
            )
            
            # Populate real Greeks data from options chain
            await self._populate_real_greeks(opportunity, data_provider)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating opportunity for {symbol}: {e}")
            return None
    
    async def _populate_real_greeks(self, opportunity: StrategyOpportunity, data_provider: IDataProvider):
        """Populate opportunity with real Greeks data from options chain."""
        try:
            # Skip if no strike prices
            if not (opportunity.short_strike or opportunity.long_strike):
                return
            
            # Get expiration date for options chain lookup
            expiration_date = opportunity.expiration
            if not expiration_date:
                return
            
            # Fetch real options chain data
            options_chain = await data_provider.get_options_chain(
                opportunity.symbol, 
                expiration=expiration_date
            )
            
            # Find the specific option contracts for our strikes
            calls_data = options_chain.get('calls', [])
            puts_data = options_chain.get('puts', [])
            
            # Look for matching strikes and get Greeks
            target_strikes = []
            if opportunity.short_strike:
                target_strikes.append(opportunity.short_strike)
            if opportunity.long_strike and opportunity.long_strike != opportunity.short_strike:
                target_strikes.append(opportunity.long_strike)
            
            total_delta = 0.0
            total_gamma = 0.0  
            total_theta = 0.0
            total_vega = 0.0
            contracts_found = 0
            
            for strike in target_strikes:
                # Check calls
                for call in calls_data:
                    if abs(call['strike'] - strike) < 0.01:  # Allow small rounding differences
                        total_delta += call.get('delta', 0.0)
                        total_gamma += call.get('gamma', 0.0)
                        total_theta += call.get('theta', 0.0)
                        total_vega += call.get('vega', 0.0)
                        contracts_found += 1
                        break
                
                # Check puts
                for put in puts_data:
                    if abs(put['strike'] - strike) < 0.01:  # Allow small rounding differences
                        total_delta += put.get('delta', 0.0)
                        total_gamma += put.get('gamma', 0.0)
                        total_theta += put.get('theta', 0.0)
                        total_vega += put.get('vega', 0.0)
                        contracts_found += 1
                        break
            
            # Update opportunity with real Greeks (average if multiple contracts)
            if contracts_found > 0:
                opportunity.delta = round(total_delta / contracts_found, 4)
                opportunity.gamma = round(total_gamma / contracts_found, 4)
                opportunity.theta = round(total_theta / contracts_found, 4)
                opportunity.vega = round(total_vega / contracts_found, 4)
                
                logger.debug(f"Updated {opportunity.symbol} Greeks from real data: Delta={opportunity.delta}, Gamma={opportunity.gamma}, Theta={opportunity.theta}, Vega={opportunity.vega}")
            
        except Exception as e:
            logger.warning(f"Could not fetch real Greeks for {opportunity.symbol}: {e}. Using defaults.")
            # Keep the default 0.0 values if real data unavailable
    
    def _apply_json_scoring(self, opportunities: List[StrategyOpportunity], config: Dict[str, Any]) -> List[StrategyOpportunity]:
        """Apply JSON-defined scoring to opportunities."""
        scoring_config = config.get('scoring', {})
        
        for opportunity in opportunities:
            score = 0.0
            
            # Base probability scoring
            prob_weight = scoring_config.get('base_probability_weight', 3.0)
            score += opportunity.probability_profit * prob_weight
            
            # Expected value scoring
            ev_multiplier = scoring_config.get('ev_multiplier', 5.0)
            if opportunity.expected_value > 0:
                score += (opportunity.expected_value / 100) * ev_multiplier
            
            # Risk-reward scoring
            risk_reward_weight = scoring_config.get('risk_reward_multiplier', 2.0)
            if opportunity.max_loss > 0:
                risk_reward = opportunity.premium * 100 / opportunity.max_loss
                score += risk_reward * risk_reward_weight
            
            # Strategy-specific bonuses
            strategy_type = config.get('strategy_type', '').upper()
            if strategy_type == 'RSI_COUPON':
                # RSI bonus (simulated)
                rsi_bonus = scoring_config.get('rsi_bonus', [])
                for bonus_rule in rsi_bonus:
                    if 'rsi_lt' in bonus_rule and 'bonus' in bonus_rule:
                        # Simulate RSI condition
                        simulated_rsi = 30 + (hash(opportunity.symbol) % 40)
                        if simulated_rsi < bonus_rule['rsi_lt']:
                            score += bonus_rule['bonus']
                            break
            
            # Apply score bounds
            score_floor = scoring_config.get('score_floor', 1.0)
            score_ceiling = scoring_config.get('score_ceiling', 10.0)
            score = max(score_floor, min(score_ceiling, score))
            
            # Round to specified decimals
            round_decimals = scoring_config.get('round_decimals', 1)
            score = round(score, round_decimals)
            
            opportunity.score = score
        
        return opportunities
    
    def _update_performance_stats(self, scan_duration: float, opportunities_found: int):
        """Update internal performance statistics."""
        self._performance_stats['opportunities_generated'] += opportunities_found
        self._performance_stats['last_scan_time'] = datetime.now()
        
        # Update average scan time
        total_scans = self._performance_stats['total_scans']
        current_avg = self._performance_stats['avg_scan_time']
        new_avg = ((current_avg * (total_scans - 1)) + scan_duration) / total_scans
        self._performance_stats['avg_scan_time'] = round(new_avg, 3)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        return {
            **self._performance_stats,
            'strategy_id': self.json_config.strategy_id,
            'strategy_type': self.json_config.strategy_type,
            'has_overrides': self.json_config.parameter_overrides is not None,
            'is_active': self.json_config.is_active
        }
    
    async def validate_opportunity(self, opportunity: StrategyOpportunity) -> bool:
        """Validate opportunity against JSON-defined criteria."""
        try:
            effective_config = self.json_config.get_effective_config()
            
            # Check basic requirements
            if opportunity.probability_profit < 0.5:  # Minimum 50% probability
                return False
            
            if opportunity.expected_value < 0:  # Must have positive expected value
                return False
            
            # Check strategy-specific validation rules
            position_params = effective_config.get('position_parameters', {})
            
            # DTE validation
            min_dte = position_params.get('min_dte', 0)
            max_dte = position_params.get('max_dte', 365)
            if not (min_dte <= opportunity.days_to_expiration <= max_dte):
                return False
            
            # Premium validation
            min_premium = position_params.get('min_premium', 0.0)
            if opportunity.premium_collected < min_premium:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return False
    
    def calculate_position_size(self, opportunity: StrategyOpportunity, account_size: float) -> int:
        """Calculate position size based on JSON-defined risk management."""
        try:
            effective_config = self.json_config.get_effective_config()
            risk_mgmt = effective_config.get('risk_management', {})
            
            # Get position sizing parameters
            max_allocation_pct = risk_mgmt.get('max_allocation_percentage', 5) / 100
            position_size_per_3k = effective_config.get('position_parameters', {}).get('position_size_per_3k', 1)
            
            # Calculate base position size
            max_risk_amount = account_size * max_allocation_pct
            position_risk = opportunity.max_loss
            
            if position_risk <= 0:
                return 1
            
            # Base calculation
            max_contracts = int(max_risk_amount / position_risk)
            
            # Scale based on account size (every $3k allows position_size_per_3k contracts)
            scaled_contracts = int((account_size / 3000) * position_size_per_3k)
            
            # Take the minimum to respect risk limits
            position_size = min(max_contracts, scaled_contracts, 10)  # Cap at 10 contracts
            
            return max(1, position_size)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 1
    
    async def initialize(self) -> bool:
        """Initialize the JSON strategy plugin."""
        try:
            logger.info(f"Initializing JSON strategy plugin: {self.json_config.strategy_id}")
            
            # Validate configuration
            effective_config = self.json_config.get_effective_config()
            if not effective_config:
                logger.error(f"Invalid configuration for strategy {self.json_config.strategy_id}")
                return False
            
            # Validate required engines are available
            if not self.engine_registry:
                logger.error(f"Engine registry not available for strategy {self.json_config.strategy_id}")
                return False
            
            # Check data provider availability
            data_provider = self.engine_registry.get_data_provider()
            if not data_provider:
                logger.warning(f"No data provider available for strategy {self.json_config.strategy_id} - will use runtime provider")
            
            # Initialize performance tracking
            self._performance_stats = {
                'total_scans': 0,
                'opportunities_generated': 0,
                'avg_scan_time': 0.0,
                'last_scan_time': None,
                'initialization_time': datetime.now()
            }
            
            logger.info(f"Successfully initialized JSON strategy: {self.json_config.strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize JSON strategy {self.json_config.strategy_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Clean up JSON strategy plugin resources."""
        try:
            logger.info(f"Cleaning up JSON strategy plugin: {self.json_config.strategy_id}")
            
            # Clear performance stats
            self._performance_stats.clear()
            
            # No persistent resources to clean up for JSON strategies
            # (data providers are managed by engine registry)
            
            logger.info(f"Successfully cleaned up JSON strategy: {self.json_config.strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup JSON strategy {self.json_config.strategy_id}: {e}")
            return False
    
    async def calculate_risk_metrics(self, opportunity: StrategyOpportunity, account_size: float = 10000) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics for an opportunity."""
        try:
            effective_config = self.json_config.get_effective_config()
            risk_mgmt = effective_config.get('risk_management', {})
            
            # Position sizing
            position_size = self.calculate_position_size(opportunity, account_size)
            total_premium = opportunity.premium_collected * position_size * 100
            total_max_loss = opportunity.max_loss * position_size
            
            # Risk metrics
            risk_reward_ratio = total_premium / total_max_loss if total_max_loss > 0 else 0
            portfolio_risk_pct = (total_max_loss / account_size) * 100
            
            # Kelly criterion for position sizing
            win_rate = opportunity.probability_profit
            avg_win = total_premium
            avg_loss = total_max_loss
            kelly_fraction = 0
            if avg_loss > 0:
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
                kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            
            # Time-based risk
            time_risk = "LOW" if opportunity.days_to_expiration > 30 else "MEDIUM" if opportunity.days_to_expiration > 14 else "HIGH"
            
            # Liquidity risk
            liquidity_risk = "LOW" if opportunity.liquidity_score > 7 else "MEDIUM" if opportunity.liquidity_score > 4 else "HIGH"
            
            # Overall risk assessment
            risk_factors = []
            if portfolio_risk_pct > risk_mgmt.get('max_allocation_percentage', 10):
                risk_factors.append("HIGH_PORTFOLIO_ALLOCATION")
            if opportunity.probability_profit < 0.6:
                risk_factors.append("LOW_WIN_RATE")
            if opportunity.days_to_expiration < 14:
                risk_factors.append("SHORT_TIME_TO_EXPIRY")
            if opportunity.liquidity_score < 5:
                risk_factors.append("LOW_LIQUIDITY")
            
            overall_risk = "HIGH" if len(risk_factors) >= 2 else "MEDIUM" if len(risk_factors) == 1 else "LOW"
            
            return {
                'position_size': position_size,
                'total_premium': round(total_premium, 2),
                'total_max_loss': round(total_max_loss, 2),
                'risk_reward_ratio': round(risk_reward_ratio, 3),
                'portfolio_risk_percentage': round(portfolio_risk_pct, 2),
                'kelly_fraction': round(kelly_fraction, 4),
                'time_risk': time_risk,
                'liquidity_risk': liquidity_risk,
                'overall_risk': overall_risk,
                'risk_factors': risk_factors,
                'max_recommended_allocation': risk_mgmt.get('max_allocation_percentage', 10),
                'strategy_type': self.json_config.strategy_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {
                'position_size': 1,
                'total_premium': 0,
                'total_max_loss': 0,
                'risk_reward_ratio': 0,
                'portfolio_risk_percentage': 0,
                'kelly_fraction': 0,
                'time_risk': 'UNKNOWN',
                'liquidity_risk': 'UNKNOWN',
                'overall_risk': 'HIGH',
                'risk_factors': ['CALCULATION_ERROR'],
                'error': str(e)
            }
    
    def _calculate_proper_dte(self, target_dte: int) -> int:
        """Calculate DTE to the next proper options expiration date (3rd Friday)."""
        today = date.today()
        
        # Find the next Friday
        days_ahead = 4 - today.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # If today is Friday or later, go to next week
            days_ahead += 7
        
        next_friday = today + timedelta(days=days_ahead)
        
        # Find the nearest 3rd Friday expiration
        current_month = next_friday.month
        current_year = next_friday.year
        
        # Calculate 3rd Friday of current month
        first_day = date(current_year, current_month, 1)
        # Find first Friday of the month
        first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
        # 3rd Friday is 2 weeks later
        third_friday = first_friday + timedelta(days=14)
        
        # If we missed this month's 3rd Friday, go to next month
        if third_friday <= today:
            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            
            first_day = date(current_year, current_month, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
            third_friday = first_friday + timedelta(days=14)
        
        # Calculate DTE to this proper expiration
        proper_dte = (third_friday - today).days
        
        # If target DTE is much different, find closer expiration
        if abs(proper_dte - target_dte) > 10:
            # Try next month's expiration
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year + 1 if current_month == 12 else current_year
            
            first_day = date(next_year, next_month, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
            next_third_friday = first_friday + timedelta(days=14)
            next_dte = (next_third_friday - today).days
            
            # Choose the closer one
            if abs(next_dte - target_dte) < abs(proper_dte - target_dte):
                return next_dte
        
        return proper_dte
    
    def _calculate_expiration_date(self, target_dte: int) -> str:
        """Calculate the actual expiration date string (3rd Friday)."""
        today = date.today()
        
        # Find the next Friday
        days_ahead = 4 - today.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # If today is Friday or later, go to next week
            days_ahead += 7
        
        next_friday = today + timedelta(days=days_ahead)
        
        # Find the nearest 3rd Friday expiration
        current_month = next_friday.month
        current_year = next_friday.year
        
        # Calculate 3rd Friday of current month
        first_day = date(current_year, current_month, 1)
        # Find first Friday of the month
        first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
        # 3rd Friday is 2 weeks later
        third_friday = first_friday + timedelta(days=14)
        
        # If we missed this month's 3rd Friday, go to next month
        if third_friday <= today:
            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            
            first_day = date(current_year, current_month, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
            third_friday = first_friday + timedelta(days=14)
        
        # If target DTE is much different, find closer expiration
        proper_dte = (third_friday - today).days
        if abs(proper_dte - target_dte) > 10:
            # Try next month's expiration
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year + 1 if current_month == 12 else current_year
            
            first_day = date(next_year, next_month, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
            next_third_friday = first_friday + timedelta(days=14)
            next_dte = (next_third_friday - today).days
            
            # Choose the closer one
            if abs(next_dte - target_dte) < abs(proper_dte - target_dte):
                third_friday = next_third_friday
        
        return third_friday.isoformat()  # Returns "2025-08-15" format