"""
Strategy-Specific Scanner
Generates opportunities based on individual strategy configurations from JSON files
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from services.universe_loader import get_universe_loader
from services.error_logging_service import log_critical_error

logger = logging.getLogger(__name__)


class StrategySpecificScanner:
    """Generates strategy-specific opportunities based on JSON configurations"""
    
    def __init__(self):
        self.universe_loader = get_universe_loader()
        self.strategy_configs = self._load_strategy_configs()
    
    def _load_strategy_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load all strategy JSON configurations"""
        configs = {}
        strategy_dir = Path('/home/arvindk/devl/dynamic-option-pilot-v2/backend/config/strategies/production')
        
        for json_file in strategy_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    config = json.load(f)
                
                strategy_type = config.get('strategy_type', json_file.stem)
                configs[strategy_type] = config
                
            except Exception as e:
                logger.error(f"Error loading strategy config {json_file}: {e}")
        
        return configs
    
    async def scan_strategy(self, strategy_type: str, sandbox_config: Dict[str, Any], 
                          test_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scan for opportunities using strategy-specific logic
        
        Args:
            strategy_type: Strategy type from JSON config
            sandbox_config: Sandbox configuration (may override JSON config)
            test_params: Additional test parameters
            
        Returns:
            Dictionary with opportunities and scan results
        """
        try:
            # Get base strategy configuration
            base_config = self.strategy_configs.get(strategy_type)
            if not base_config:
                raise RuntimeError(f"Strategy configuration not found for {strategy_type}")
            
            # Merge configurations (sandbox overrides base)
            merged_config = self._merge_configs(base_config, sandbox_config)
            
            # Get symbols for scanning
            symbols = await self._get_strategy_symbols(merged_config, test_params)
            if not symbols:
                raise RuntimeError(f"No symbols available for strategy {strategy_type}")
            
            # Generate opportunities based on strategy type
            opportunities = await self._generate_strategy_opportunities(
                strategy_type, merged_config, symbols, test_params
            )
            
            return {
                'success': True,
                'opportunities_count': len(opportunities),
                'opportunities': opportunities,
                'strategy_type': strategy_type,
                'symbols_scanned': symbols,
                'scan_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await log_critical_error(
                error_type="strategy_scan_failure",
                message=f"Strategy-specific scan failed for {strategy_type}: {str(e)}",
                details={
                    "strategy_type": strategy_type,
                    "error": str(e)
                },
                service="strategy_specific_scanner",
                severity="HIGH"
            )
            
            return {
                'success': False,
                'error': str(e),
                'opportunities_count': 0,
                'opportunities': [],
                'strategy_type': strategy_type
            }
    
    def _merge_configs(self, base_config: Dict[str, Any], 
                      sandbox_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base strategy config with sandbox overrides"""
        merged = base_config.copy()
        
        # Deep merge strategy-specific sections
        for section in ['position_parameters', 'entry_signals', 'scoring', 'universe', 'exit_rules']:
            if section in sandbox_config:
                if section in merged:
                    merged[section].update(sandbox_config[section])
                else:
                    merged[section] = sandbox_config[section]
        
        return merged
    
    async def _get_strategy_symbols(self, config: Dict[str, Any], 
                                  test_params: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get symbols for strategy scanning"""
        
        # If test params specify symbols, use those
        if test_params and test_params.get('symbols'):
            return test_params['symbols']
        
        # Get from universe configuration
        universe_config = config.get('universe', {})
        
        # Try universe file first
        if 'universe_file' in universe_config:
            universe_name = Path(universe_config['universe_file']).stem
            try:
                symbols = self.universe_loader.get_universe(universe_name)
                if symbols:
                    return symbols[:universe_config.get('max_symbols', 10)]
            except Exception as e:
                logger.warning(f"Failed to load universe from file: {e}")
        
        # Try universe name
        if 'universe_name' in universe_config:
            universe_name = universe_config['universe_name']
            try:
                symbols = self.universe_loader.get_universe(universe_name)
                if symbols:
                    return symbols[:universe_config.get('max_symbols', 10)]
            except Exception as e:
                logger.warning(f"Failed to load universe {universe_name}: {e}")
        
        # Try primary_symbols as fallback
        if 'primary_symbols' in universe_config:
            primary_symbols = universe_config['primary_symbols']
            if isinstance(primary_symbols, list) and primary_symbols:
                max_symbols = universe_config.get('max_symbols', len(primary_symbols))
                return primary_symbols[:max_symbols]
        
        # Try fallback to default symbols for testing
        if test_params or not universe_config:
            logger.warning(f"No universe configuration found, using default symbols for testing")
            return ['SPY', 'QQQ', 'IWM']  # Safe default for testing
        
        # NO FALLBACK for production - explicit error
        raise RuntimeError(f"No valid universe configuration found in strategy config")
    
    async def _generate_strategy_opportunities(self, strategy_type: str, config: Dict[str, Any], 
                                            symbols: List[str], test_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate opportunities specific to strategy type"""
        
        opportunities = []
        max_opportunities = test_params.get('max_opportunities', 5) if test_params else 5
        
        # Get strategy-specific parameters
        position_params = config.get('position_parameters', {})
        entry_signals = config.get('entry_signals', {})
        scoring = config.get('scoring', {})
        
        for i, symbol in enumerate(symbols[:max_opportunities]):
            if strategy_type == 'THETA_HARVESTING':
                opportunity = await self._generate_theta_harvesting_opportunity(
                    symbol, position_params, entry_signals, scoring, i
                )
            elif strategy_type == 'RSI_COUPON':
                opportunity = await self._generate_rsi_coupon_opportunity(
                    symbol, position_params, entry_signals, scoring, i
                )
            elif strategy_type == 'IRON_CONDOR':
                opportunity = await self._generate_iron_condor_opportunity(
                    symbol, position_params, entry_signals, scoring, i
                )
            elif strategy_type == 'PROTECTIVE_PUT':
                opportunity = await self._generate_protective_put_opportunity(
                    symbol, position_params, entry_signals, scoring, i
                )
            elif strategy_type in ['STRANGLE', 'STRADDLE']:
                opportunity = await self._generate_volatility_opportunity(
                    symbol, position_params, entry_signals, scoring, i, strategy_type
                )
            else:
                # Generic opportunity for other strategies
                opportunity = await self._generate_generic_opportunity(
                    symbol, position_params, entry_signals, scoring, i, strategy_type
                )
            
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _generate_theta_harvesting_opportunity(self, symbol: str, position_params: Dict, 
                                                   entry_signals: Dict, scoring: Dict, index: int) -> Dict[str, Any]:
        """Generate ThetaCrop Weekly specific opportunity"""
        
        target_dte_range = position_params.get('target_dte_range', [5, 10])
        delta_target = position_params.get('delta_target', 0.2)
        wing_widths = position_params.get('wing_widths', [2, 3, 4])
        min_credit_ratio = position_params.get('min_credit_ratio', 0.15)
        
        # Simulate realistic values based on strategy parameters
        dte = random.choice(target_dte_range)
        wing_width = random.choice(wing_widths)
        
        # Simulate underlying price
        base_prices = {'SPY': 540, 'QQQ': 410, 'IWM': 195, 'TLT': 94, 'GLD': 185}
        underlying_price = base_prices.get(symbol, 100) + random.uniform(-5, 5)
        
        # Calculate strikes based on delta target
        delta_offset = underlying_price * delta_target
        short_call_strike = underlying_price + delta_offset
        short_put_strike = underlying_price - delta_offset
        long_call_strike = short_call_strike + wing_width
        long_put_strike = short_put_strike - wing_width
        
        # Calculate credit based on wing width and min ratio
        max_loss = wing_width * 100  # Per contract
        min_credit = max_loss * min_credit_ratio
        credit = min_credit + random.uniform(0, min_credit * 0.5)
        
        # Calculate probability based on strategy scoring
        base_prob_weight = scoring.get('base_probability_weight', 4.0)
        theta_bonus = 1.5 if dte <= 7 else 1.0
        probability_profit = min(0.85, 0.65 + (credit / max_loss) * 0.2) * theta_bonus
        
        return {
            'id': f"theta_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': 'THETA_HARVESTING',
            'underlying_price': round(underlying_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'legs': [
                {
                    'action': 'SELL',
                    'option_type': 'CALL',
                    'strike': round(short_call_strike, 2),
                    'delta': round(delta_target, 3)
                },
                {
                    'action': 'BUY',
                    'option_type': 'CALL', 
                    'strike': round(long_call_strike, 2),
                    'delta': round(delta_target * 0.5, 3)
                },
                {
                    'action': 'SELL',
                    'option_type': 'PUT',
                    'strike': round(short_put_strike, 2),
                    'delta': round(-delta_target, 3)
                },
                {
                    'action': 'BUY',
                    'option_type': 'PUT',
                    'strike': round(long_put_strike, 2),
                    'delta': round(-delta_target * 0.5, 3)
                }
            ],
            'premium': round(credit, 2),
            'max_profit': round(credit, 2),
            'max_loss': round(max_loss - credit, 2),
            'probability_profit': round(probability_profit, 3),
            'expected_value': round(credit * probability_profit - (max_loss - credit) * (1 - probability_profit), 2),
            'break_even_high': round(short_call_strike + credit/100, 2),
            'break_even_low': round(short_put_strike - credit/100, 2),
            'theta': round(-credit * 0.15, 2),
            'score': round(min(10.0, max(1.0, probability_profit * base_prob_weight + theta_bonus)), 1),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_rsi_coupon_opportunity(self, symbol: str, position_params: Dict,
                                             entry_signals: Dict, scoring: Dict, index: int) -> Dict[str, Any]:
        """Generate RSI Coupon specific opportunity"""
        
        target_dtes = position_params.get('target_dtes', [20, 30, 45])
        delta_range = position_params.get('preferred_delta_range', [0.25, 0.40])
        min_prob_profit = position_params.get('min_probability_profit', 0.65)
        
        # RSI-specific parameters
        rsi_below = entry_signals.get('rsi_below', 45)
        
        # Simulate RSI conditions
        simulated_rsi = random.uniform(25, rsi_below)
        dte = random.choice(target_dtes)
        delta = random.uniform(delta_range[0], delta_range[1])
        
        # Base prices for common symbols
        base_prices = {'SPY': 540, 'QQQ': 410, 'AAPL': 180, 'MSFT': 350, 'GOOGL': 140}
        underlying_price = base_prices.get(symbol, 120) + random.uniform(-10, 5)  # Slight downward bias for oversold
        
        # Calculate strike for bullish reversal play
        strike = underlying_price * (1 - delta)  # OTM put or ATM call
        
        # Premium based on volatility and time
        premium = strike * 0.03 * (dte / 30) * (1 + (45 - simulated_rsi) / 100)
        
        # RSI bonus in scoring
        rsi_bonus = 2.0 if simulated_rsi < 25 else 1.5 if simulated_rsi < 30 else 1.0
        probability_profit = max(min_prob_profit, 0.65 + rsi_bonus * 0.05)
        
        return {
            'id': f"rsi_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': 'RSI_COUPON',
            'underlying_price': round(underlying_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'legs': [
                {
                    'action': 'BUY',
                    'option_type': 'CALL',  # Bullish reversal
                    'strike': round(strike, 2),
                    'delta': round(delta, 3)
                }
            ],
            'premium': round(premium, 2),
            'max_profit': 'Unlimited',
            'max_loss': round(premium, 2),
            'probability_profit': round(probability_profit, 3),
            'break_even': round(strike + premium, 2),
            'rsi_level': round(simulated_rsi, 1),
            'reversal_signal': 'OVERSOLD' if simulated_rsi < 30 else 'BULLISH',
            'score': round(min(10.0, max(2.0, probability_profit * scoring.get('base_probability_weight', 5.0) * rsi_bonus)), 1),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_iron_condor_opportunity(self, symbol: str, position_params: Dict,
                                              entry_signals: Dict, scoring: Dict, index: int) -> Dict[str, Any]:
        """Generate Iron Condor specific opportunity"""
        
        delta_target = position_params.get('delta_target', 0.15)
        min_dte = position_params.get('min_dte', 15)
        max_dte = position_params.get('max_dte', 45)
        max_wing_width = position_params.get('max_wing_width', 10)
        min_total_credit = position_params.get('min_total_credit', 0.30)
        
        dte = random.randint(min_dte, max_dte)
        wing_width = random.randint(5, max_wing_width)
        
        base_prices = {'SPY': 540, 'QQQ': 410, 'IWM': 195, 'DIA': 420}
        underlying_price = base_prices.get(symbol, 150) + random.uniform(-3, 3)
        
        # Calculate strikes for iron condor
        delta_offset = underlying_price * delta_target
        short_put_strike = underlying_price - delta_offset
        long_put_strike = short_put_strike - wing_width
        short_call_strike = underlying_price + delta_offset
        long_call_strike = short_call_strike + wing_width
        
        # Calculate credit
        total_credit = max(min_total_credit, wing_width * 0.25 + random.uniform(0, 0.5))
        max_loss = wing_width * 100 - total_credit * 100
        
        prob_weight = scoring.get('probability_weight', 4.0)
        probability_profit = min(0.80, 0.60 + (total_credit / wing_width) * 0.15)
        
        return {
            'id': f"ic_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': 'IRON_CONDOR',
            'underlying_price': round(underlying_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'legs': [
                {'action': 'SELL', 'option_type': 'PUT', 'strike': round(short_put_strike, 2), 'delta': round(-delta_target, 3)},
                {'action': 'BUY', 'option_type': 'PUT', 'strike': round(long_put_strike, 2), 'delta': round(-delta_target * 0.5, 3)},
                {'action': 'SELL', 'option_type': 'CALL', 'strike': round(short_call_strike, 2), 'delta': round(delta_target, 3)},
                {'action': 'BUY', 'option_type': 'CALL', 'strike': round(long_call_strike, 2), 'delta': round(delta_target * 0.5, 3)}
            ],
            'premium': round(total_credit, 2),
            'max_profit': round(total_credit, 2),
            'max_loss': round(max_loss / 100, 2),
            'probability_profit': round(probability_profit, 3),
            'profit_zone_width': round(short_call_strike - short_put_strike, 2),
            'score': round(min(10.0, max(1.0, probability_profit * prob_weight)), 1),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_protective_put_opportunity(self, symbol: str, position_params: Dict,
                                                 entry_signals: Dict, scoring: Dict, index: int) -> Dict[str, Any]:
        """Generate Protective Put specific opportunity"""
        
        max_premium_pct = position_params.get('max_premium_pct_equity', 0.02)
        min_protection_level = position_params.get('min_protection_level', 0.90)
        
        base_prices = {'AAPL': 180, 'MSFT': 350, 'GOOGL': 140, 'AMZN': 145, 'TSLA': 250}
        stock_price = base_prices.get(symbol, 200) + random.uniform(-15, 15)
        
        # Calculate put strike for protection level
        put_strike = stock_price * min_protection_level
        premium = stock_price * max_premium_pct * random.uniform(0.5, 1.5)
        
        dte = random.randint(30, 60)
        
        return {
            'id': f"pp_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': 'PROTECTIVE_PUT',
            'stock_price': round(stock_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'legs': [
                {'action': 'BUY', 'option_type': 'PUT', 'strike': round(put_strike, 2), 'delta': -0.30}
            ],
            'insurance_cost': round(premium, 2),
            'protection_level': round(min_protection_level * 100, 1),
            'max_loss_without_put': round(stock_price - put_strike, 2),
            'max_loss_with_put': round(premium, 2),
            'break_even': round(stock_price + premium, 2),
            'score': round(random.uniform(6.0, 9.0), 1),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_volatility_opportunity(self, symbol: str, position_params: Dict,
                                             entry_signals: Dict, scoring: Dict, index: int, strategy_type: str) -> Dict[str, Any]:
        """Generate Straddle/Strangle opportunities"""
        
        volatility_min = entry_signals.get('volatility_min', 0.25)
        max_premium_cost = position_params.get('max_premium_cost', 5.0)
        
        base_prices = {'TSLA': 250, 'NVDA': 450, 'AMD': 110, 'NFLX': 380}
        underlying_price = base_prices.get(symbol, 200) + random.uniform(-20, 20)
        
        # Simulate high volatility environment
        iv_rank = random.uniform(60, 90)  # High volatility
        dte = random.randint(20, 40)
        
        if strategy_type == 'STRADDLE':
            # ATM straddle
            strike = underlying_price
            premium = underlying_price * 0.05 * (iv_rank / 50) * (dte / 30)
            legs = [
                {'action': 'BUY', 'option_type': 'CALL', 'strike': round(strike, 2), 'delta': 0.50},
                {'action': 'BUY', 'option_type': 'PUT', 'strike': round(strike, 2), 'delta': -0.50}
            ]
        else:  # STRANGLE
            # OTM strangle
            call_strike = underlying_price * 1.05
            put_strike = underlying_price * 0.95
            premium = underlying_price * 0.03 * (iv_rank / 50) * (dte / 30)
            legs = [
                {'action': 'BUY', 'option_type': 'CALL', 'strike': round(call_strike, 2), 'delta': 0.30},
                {'action': 'BUY', 'option_type': 'PUT', 'strike': round(put_strike, 2), 'delta': -0.30}
            ]
        
        return {
            'id': f"{strategy_type.lower()}_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': strategy_type,
            'underlying_price': round(underlying_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'legs': legs,
            'premium_paid': round(premium, 2),
            'max_loss': round(premium, 2),
            'iv_rank': round(iv_rank, 1),
            'expected_move': round(underlying_price * 0.15, 2),
            'break_even_high': round(underlying_price + premium, 2),
            'break_even_low': round(underlying_price - premium, 2),
            'score': round(min(10.0, max(3.0, (iv_rank / 50) * scoring.get('volatility_weight', 3.0))), 1),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_generic_opportunity(self, symbol: str, position_params: Dict,
                                          entry_signals: Dict, scoring: Dict, index: int, strategy_type: str) -> Dict[str, Any]:
        """Generate generic opportunity for other strategy types"""
        
        max_opportunities = position_params.get('max_opportunities', 5)
        dte = random.randint(15, 45)
        
        base_prices = {'SPY': 540, 'QQQ': 410, 'default': 150}
        underlying_price = base_prices.get(symbol, base_prices['default']) + random.uniform(-10, 10)
        
        premium = underlying_price * random.uniform(0.01, 0.05)
        probability_profit = random.uniform(0.60, 0.80)
        
        return {
            'id': f"{strategy_type.lower()}_{symbol}_{index}_{int(datetime.utcnow().timestamp())}",
            'symbol': symbol,
            'strategy_type': strategy_type,
            'underlying_price': round(underlying_price, 2),
            'expiration_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d'),
            'days_to_expiration': dte,
            'premium': round(premium, 2),
            'probability_profit': round(probability_profit, 3),
            'score': round(random.uniform(5.0, 8.5), 1),
            'created_at': datetime.utcnow().isoformat()
        }


# Global instance
_strategy_scanner = None

def get_strategy_specific_scanner() -> StrategySpecificScanner:
    """Get global strategy-specific scanner instance"""
    global _strategy_scanner
    if _strategy_scanner is None:
        _strategy_scanner = StrategySpecificScanner()
    return _strategy_scanner