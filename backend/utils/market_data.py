"""
Market Data Utilities - Pure functions for data fetching and processing
Extracted from orchestrator and trading.py for better testability
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class MarketData:
    """Standardized market data container"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    iv_rank: Optional[float] = None
    beta: Optional[float] = None


@dataclass 
class HistoricalData:
    """Historical price and volume data"""
    symbol: str
    data: pd.DataFrame  # OHLCV format
    period: str  # '1d', '1h', etc.


class MarketDataClient:
    """Abstraction layer for market data - can switch providers easily"""
    
    def __init__(self, primary_provider, fallback_provider=None):
        self.primary = primary_provider
        self.fallback = fallback_provider
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Get current quote with fallback logic"""
        try:
            return await self.primary.get_quote(symbol)
        except Exception:
            if self.fallback:
                return await self.fallback.get_quote(symbol)
            raise
    
    async def get_historical(self, symbol: str, period: str = "1y", interval: str = "1d") -> HistoricalData:
        """Get historical data with caching"""
        try:
            data = await self.primary.get_historical(symbol, period, interval)
            return HistoricalData(symbol=symbol, data=data, period=period)
        except Exception:
            if self.fallback:
                data = await self.fallback.get_historical(symbol, period, interval)
                return HistoricalData(symbol=symbol, data=data, period=period)
            raise


def calculate_iv_rank(current_iv: float, historical_ivs: List[float], periods: int = 252) -> float:
    """Calculate IV rank - percentile of current IV vs historical"""
    if not historical_ivs or len(historical_ivs) < periods:
        return 50.0  # Default to 50th percentile
    
    recent_ivs = historical_ivs[-periods:]
    rank = sum(1 for iv in recent_ivs if current_iv >= iv) / len(recent_ivs) * 100
    return round(rank, 1)


def calculate_beta(symbol_returns: pd.Series, market_returns: pd.Series, periods: int = 252) -> float:
    """Calculate beta vs market (typically SPY)"""
    if len(symbol_returns) < periods or len(market_returns) < periods:
        return 1.0  # Default beta
    
    recent_symbol = symbol_returns.tail(periods)
    recent_market = market_returns.tail(periods)
    
    covariance = recent_symbol.cov(recent_market)
    market_variance = recent_market.var()
    
    return round(covariance / market_variance if market_variance > 0 else 1.0, 2)