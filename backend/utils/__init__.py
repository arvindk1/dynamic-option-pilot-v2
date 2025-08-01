"""
Utils Package - Pure functions and utilities for options trading
Extracted from monolithic modules for better testability and maintainability
"""

from .market_data import MarketData, HistoricalData, MarketDataClient
from .option_pricing import (
    calculate_realistic_spread_credit,
    calculate_spread_greeks,
    calculate_probability_of_profit,
    SpreadPricingEngine,
    OptionQuote,
    SpreadQuote
)
from .signal_analysis import (
    TechnicalIndicators,
    MarketSignals,
    SignalAnalyzer,
    ProbabilityCalculator,
    determine_trade_setup
)
from .expirations import (
    OptionExpiration,
    ExpirationType,
    ExpirationGenerator,
    ExpirationCalendar
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
    "ExpirationCalendar"
]