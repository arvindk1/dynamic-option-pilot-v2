"""
Utils Package - Pure functions and utilities for options trading
Extracted from monolithic modules for better testability and maintainability
"""

from .expirations import (
    ExpirationCalendar,
    ExpirationGenerator,
    ExpirationType,
    OptionExpiration,
)
from .market_data import HistoricalData, MarketData, MarketDataClient
from .option_pricing import (
    OptionQuote,
    SpreadPricingEngine,
    SpreadQuote,
    calculate_probability_of_profit,
    calculate_realistic_spread_credit,
    calculate_spread_greeks,
)
from .signal_analysis import (
    MarketSignals,
    ProbabilityCalculator,
    SignalAnalyzer,
    TechnicalIndicators,
    determine_trade_setup,
)

__version__ = "1.0.0"
__all__ = [
    # Market Data
    "MarketData",
    "HistoricalData",
    "MarketDataClient",
    # Options Pricing
    "calculate_realistic_spread_credit",
    "calculate_spread_greeks",
    "calculate_probability_of_profit",
    "SpreadPricingEngine",
    "OptionQuote",
    "SpreadQuote",
    # Signal Analysis
    "TechnicalIndicators",
    "MarketSignals",
    "SignalAnalyzer",
    "ProbabilityCalculator",
    "determine_trade_setup",
    # Expirations
    "OptionExpiration",
    "ExpirationType",
    "ExpirationGenerator",
    "ExpirationCalendar",
]
