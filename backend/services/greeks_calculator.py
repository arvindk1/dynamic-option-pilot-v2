"""
Options Greeks Calculator using Black-Scholes Model
Calculates Delta, Gamma, Theta, Vega for options positions
"""

import math
from typing import Dict, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def norm_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal distribution"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def norm_pdf(x: float) -> float:
    """Probability density function for standard normal distribution"""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

class GreeksCalculator:
    """Calculate options Greeks using Black-Scholes model"""
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize Greeks calculator
        
        Args:
            risk_free_rate: Risk-free interest rate (default 5%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_greeks(self, 
                        spot_price: float,
                        strike_price: float, 
                        time_to_expiration: float,
                        volatility: float,
                        option_type: str = 'CALL',
                        risk_free_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate all Greeks for an option
        
        Args:
            spot_price: Current underlying price
            strike_price: Option strike price
            time_to_expiration: Years to expiration (e.g., 30 days = 30/365)
            volatility: Implied volatility (e.g., 0.20 for 20%)
            option_type: 'CALL' or 'PUT'
            risk_free_rate: Risk-free rate (overrides default)
            
        Returns:
            Dict with delta, gamma, theta, vega, rho
        """
        try:
            if risk_free_rate is None:
                risk_free_rate = self.risk_free_rate
            
            # Handle edge cases
            if time_to_expiration <= 0:
                # Option expired or expires today
                if option_type.upper() == 'CALL':
                    delta = 1.0 if spot_price > strike_price else 0.0
                else:  # PUT
                    delta = -1.0 if spot_price < strike_price else 0.0
                
                return {
                    'delta': delta,
                    'gamma': 0.0,
                    'theta': 0.0,
                    'vega': 0.0,
                    'rho': 0.0
                }
            
            if volatility <= 0:
                volatility = 0.01  # Minimum volatility to avoid division by zero
            
            # Black-Scholes calculations
            d1 = (math.log(spot_price / strike_price) + 
                  (risk_free_rate + 0.5 * volatility**2) * time_to_expiration) / \
                 (volatility * math.sqrt(time_to_expiration))
            
            d2 = d1 - volatility * math.sqrt(time_to_expiration)
            
            # Standard normal CDF and PDF values
            N_d1 = norm_cdf(d1)
            N_d2 = norm_cdf(d2)
            n_d1 = norm_pdf(d1)  # PDF for gamma and vega
            
            # Calculate Greeks
            if option_type.upper() == 'CALL':
                delta = N_d1
                theta = (-spot_price * n_d1 * volatility / (2 * math.sqrt(time_to_expiration)) -
                        risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiration) * N_d2) / 365
                rho = strike_price * time_to_expiration * math.exp(-risk_free_rate * time_to_expiration) * N_d2 / 100
            else:  # PUT
                delta = N_d1 - 1
                theta = (-spot_price * n_d1 * volatility / (2 * math.sqrt(time_to_expiration)) +
                        risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiration) * (1 - N_d2)) / 365
                rho = -strike_price * time_to_expiration * math.exp(-risk_free_rate * time_to_expiration) * (1 - N_d2) / 100
            
            # Gamma and Vega are the same for calls and puts
            gamma = n_d1 / (spot_price * volatility * math.sqrt(time_to_expiration))
            vega = spot_price * n_d1 * math.sqrt(time_to_expiration) / 100  # Divided by 100 for percentage
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),  # Gamma is typically small
                'theta': round(theta, 4),   # Theta per day
                'vega': round(vega, 4),     # Vega per 1% volatility change
                'rho': round(rho, 4)        # Rho per 1% interest rate change
            }
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {
                'delta': 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }
    
    def calculate_portfolio_greeks(self, positions: list) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for a portfolio of positions
        
        Args:
            positions: List of position dicts with Greeks and quantities
            
        Returns:
            Dict with total portfolio Greeks
        """
        try:
            portfolio_greeks = {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_theta': 0.0,
                'total_vega': 0.0,
                'total_rho': 0.0
            }
            
            for position in positions:
                quantity = position.get('quantity', 0)
                
                # Weight Greeks by position size
                portfolio_greeks['total_delta'] += position.get('delta', 0) * quantity
                portfolio_greeks['total_gamma'] += position.get('gamma', 0) * quantity
                portfolio_greeks['total_theta'] += position.get('theta', 0) * quantity
                portfolio_greeks['total_vega'] += position.get('vega', 0) * quantity
                portfolio_greeks['total_rho'] += position.get('rho', 0) * quantity
            
            # Round results
            for key in portfolio_greeks:
                portfolio_greeks[key] = round(portfolio_greeks[key], 4)
            
            return portfolio_greeks
            
        except Exception as e:
            logger.error(f"Error calculating portfolio Greeks: {e}")
            return {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_theta': 0.0,
                'total_vega': 0.0,
                'total_rho': 0.0
            }
    
    def calculate_days_to_expiration(self, expiration_date: str) -> float:
        """
        Calculate days to expiration as a fraction of a year
        
        Args:
            expiration_date: ISO format date string
            
        Returns:
            Years to expiration (e.g., 30 days = 30/365 = 0.082)
        """
        try:
            if not expiration_date or expiration_date == 'N/A':
                return 0.0
            
            # Parse expiration date
            if 'T' in expiration_date:
                # Remove timezone suffix if present and add UTC
                clean_date = expiration_date.replace('Z', '').replace('+00:00', '')
                exp_date = datetime.fromisoformat(clean_date).replace(tzinfo=timezone.utc)
            else:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            
            # Calculate days to expiration
            now = datetime.now(timezone.utc)
            days_to_exp = (exp_date - now).total_seconds() / (24 * 3600)
            
            # Convert to years (using 365 days per year)
            return max(0.0, days_to_exp / 365.0)
            
        except Exception as e:
            logger.error(f"Error calculating days to expiration from {expiration_date}: {e}")
            return 0.0

# Global calculator instance
_greeks_calculator = None

def get_greeks_calculator() -> GreeksCalculator:
    """Get global Greeks calculator instance"""
    global _greeks_calculator
    if _greeks_calculator is None:
        _greeks_calculator = GreeksCalculator()
    return _greeks_calculator

def calculate_position_greeks(position: Dict, underlying_price: float, implied_volatility: float = 0.20) -> Dict:
    """
    Convenience function to calculate Greeks for a single position
    
    Args:
        position: Position dict with strike, expiration, type, etc.
        underlying_price: Current underlying price
        implied_volatility: Estimated IV (default 20%)
        
    Returns:
        Position dict updated with Greeks
    """
    calculator = get_greeks_calculator()
    
    try:
        # Extract position details
        strike = position.get('strike')
        expiration = position.get('expiration')
        option_type = position.get('type', 'STOCK')
        
        # Skip if not an option
        if option_type not in ['CALL', 'PUT'] or not strike or not expiration:
            return position
        
        # Calculate time to expiration
        time_to_exp = calculator.calculate_days_to_expiration(expiration)
        
        if time_to_exp <= 0:
            # Expired option
            position.update({
                'delta': 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            })
        else:
            # Calculate Greeks
            greeks = calculator.calculate_greeks(
                spot_price=underlying_price,
                strike_price=strike,
                time_to_expiration=time_to_exp,
                volatility=implied_volatility,
                option_type=option_type
            )
            
            position.update(greeks)
        
        return position
        
    except Exception as e:
        logger.error(f"Error calculating Greeks for position {position.get('symbol', 'unknown')}: {e}")
        # Return position with zero Greeks if calculation fails
        position.update({
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        })
        return position