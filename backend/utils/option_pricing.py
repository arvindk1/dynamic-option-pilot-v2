"""
Options Pricing Utilities - Realistic pricing models
Incorporates the fixes we made for market-accurate spread credits
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple


@dataclass
class OptionQuote:
    """Individual option quote"""

    symbol: str
    strike: float
    expiration: datetime
    option_type: str  # 'CALL' or 'PUT'
    bid: float
    ask: float
    mid: float
    volume: int
    open_interest: int
    implied_volatility: float


@dataclass
class SpreadQuote:
    """Spread pricing information"""

    short_leg: OptionQuote
    long_leg: OptionQuote
    net_credit: float
    max_profit: float
    max_loss: float
    breakeven: float
    pop: float  # Probability of profit


def calculate_realistic_spread_credit(
    short_strike: float,
    long_strike: float,
    current_price: float,
    dte: int,
    option_type: str,
) -> float:
    """
    Calculate realistic credit for spread based on actual market behavior
    This is our corrected pricing model from the regression testing
    """
    spread_width = abs(short_strike - long_strike)

    # Calculate distance from underlying (moneyness)
    if option_type.upper() == "PUT":
        distance_from_strike = (current_price - short_strike) / current_price
    else:  # CALL
        distance_from_strike = (short_strike - current_price) / current_price

    # Realistic credit ratios based on actual market observation
    if distance_from_strike > 0.15:  # Far OTM
        credit_ratio = 0.01
    elif distance_from_strike > 0.10:  # Moderately OTM
        credit_ratio = 0.03
    elif distance_from_strike > 0.05:  # Slightly OTM
        credit_ratio = 0.08
    elif distance_from_strike > 0.00:  # Near ATM
        credit_ratio = 0.15
    else:  # ATM or ITM
        credit_ratio = 0.25

    # Time decay impact
    time_factor = math.sqrt(max(1, dte) / 365)

    # Market reality adjustment
    market_reality_discount = 0.6

    # Basic calculation
    base_credit = spread_width * credit_ratio * time_factor * market_reality_discount

    # Constraints
    min_credit = 0.02  # $2 minimum
    max_credit = spread_width * 0.30  # Never more than 30% of width

    return round(max(min_credit, min(base_credit, max_credit)), 2)


def calculate_spread_greeks(
    short_strike: float,
    long_strike: float,
    underlying_price: float,
    dte: int,
    option_type: str,
    iv: float = 0.20,
) -> Dict[str, float]:
    """Calculate net Greeks for spread position"""
    # Simplified Greeks calculation for spreads
    time_to_expiry = dte / 365.0

    # Delta approximation
    if option_type.upper() == "PUT":
        short_delta = -max(
            0.01, min(0.99, (underlying_price - short_strike) / underlying_price)
        )
        long_delta = -max(
            0.01, min(0.99, (underlying_price - long_strike) / underlying_price)
        )
    else:
        short_delta = max(
            0.01, min(0.99, (short_strike - underlying_price) / underlying_price)
        )
        long_delta = max(
            0.01, min(0.99, (long_strike - underlying_price) / underlying_price)
        )

    net_delta = short_delta - long_delta

    # Gamma (rate of delta change)
    gamma = abs(net_delta) * 0.1 / time_to_expiry if time_to_expiry > 0 else 0

    # Theta (time decay) - negative for long positions, positive for short spreads
    theta = (
        -abs(net_delta) * iv * 0.1 / math.sqrt(time_to_expiry)
        if time_to_expiry > 0
        else 0
    )

    # Vega (volatility sensitivity)
    vega = abs(net_delta) * math.sqrt(time_to_expiry) * 0.1

    return {
        "delta": round(net_delta, 4),
        "gamma": round(gamma, 4),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
    }


def calculate_probability_of_profit(
    short_strike: float,
    underlying_price: float,
    dte: int,
    option_type: str,
    credit: float,
    iv: float = 0.20,
) -> float:
    """Estimate probability of profit for credit spread"""

    # Calculate breakeven point
    if option_type.upper() == "PUT":
        breakeven = short_strike - credit
        # For put spreads, profit if price stays above breakeven
        distance_to_breakeven = (underlying_price - breakeven) / underlying_price
    else:
        breakeven = short_strike + credit
        # For call spreads, profit if price stays below breakeven
        distance_to_breakeven = (breakeven - underlying_price) / underlying_price

    # Simple normal distribution approximation
    # Larger distance = higher probability
    time_factor = math.sqrt(dte / 365.0)
    volatility_adjusted_distance = distance_to_breakeven / (iv * time_factor)

    # Convert to probability (rough approximation)
    if volatility_adjusted_distance > 2:
        prob = 0.95
    elif volatility_adjusted_distance > 1:
        prob = 0.80
    elif volatility_adjusted_distance > 0.5:
        prob = 0.65
    elif volatility_adjusted_distance > 0:
        prob = 0.55
    else:
        prob = 0.45

    return round(prob, 3)


class SpreadPricingEngine:
    """Main pricing engine for option spreads"""

    def __init__(self, risk_free_rate: float = 0.045):
        self.risk_free_rate = risk_free_rate

    def price_credit_spread(
        self,
        symbol: str,
        short_strike: float,
        long_strike: float,
        underlying_price: float,
        expiration: datetime,
        option_type: str,
    ) -> SpreadQuote:
        """Price a credit spread with all metrics"""

        dte = (expiration - datetime.now()).days

        # Core pricing
        credit = calculate_realistic_spread_credit(
            short_strike, long_strike, underlying_price, dte, option_type
        )

        # Risk metrics
        spread_width = abs(short_strike - long_strike)
        max_profit = credit
        max_loss = spread_width - credit

        # Breakeven
        if option_type.upper() == "PUT":
            breakeven = short_strike - credit
        else:
            breakeven = short_strike + credit

        # Probability
        pop = calculate_probability_of_profit(
            short_strike, underlying_price, dte, option_type, credit
        )

        # Create mock option quotes (in real system, would fetch from broker)
        short_quote = OptionQuote(
            symbol=f"{symbol}_{short_strike}{option_type[0]}",
            strike=short_strike,
            expiration=expiration,
            option_type=option_type,
            bid=credit * 0.8,  # Approximate
            ask=credit * 1.2,
            mid=credit,
            volume=100,
            open_interest=500,
            implied_volatility=0.20,
        )

        long_quote = OptionQuote(
            symbol=f"{symbol}_{long_strike}{option_type[0]}",
            strike=long_strike,
            expiration=expiration,
            option_type=option_type,
            bid=0.01,  # Far OTM protection
            ask=0.05,
            mid=0.03,
            volume=50,
            open_interest=200,
            implied_volatility=0.18,
        )

        return SpreadQuote(
            short_leg=short_quote,
            long_leg=long_quote,
            net_credit=credit,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven=breakeven,
            pop=pop,
        )
