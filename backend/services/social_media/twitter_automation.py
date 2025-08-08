"""
Twitter Automation Service for Dynamic Options Pilot v2
Real-time market intelligence and educational content automation
"""
import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import yfinance as yf

logger = logging.getLogger(__name__)

class MarketSession(Enum):
    PRE_MARKET = "pre_market"
    REGULAR_HOURS = "regular_hours"  
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"

@dataclass
class VIXData:
    current: float
    previous_close: float
    change: float
    change_percent: float
    context: str
    regime: str
    historical_percentile: float

@dataclass
class MarketSnapshot:
    spy_price: float
    spy_change: float
    spy_change_percent: float
    vix_data: VIXData
    session: MarketSession
    timestamp: datetime

class TwitterAutomationService:
    """Professional Twitter automation for options trading intelligence."""
    
    def __init__(self):
        self.setup_market_data()
        
    def setup_market_data(self):
        """Initialize market data connections."""
        self.spy_ticker = yf.Ticker("SPY")
        self.vix_ticker = yf.Ticker("^VIX")
        self.qqq_ticker = yf.Ticker("QQQ")
        logger.info("✅ Market data tickers initialized")
    
    async def get_vix_data(self) -> VIXData:
        """Get comprehensive VIX data with context."""
        try:
            # Get current VIX data using alternative method
            vix_hist = yf.download("^VIX", period="5d", interval="1d", progress=False)
            if vix_hist.empty:
                raise ValueError("No VIX data available")
            
            current_vix = float(vix_hist['Close'].iloc[-1])
            previous_close = float(vix_hist['Close'].iloc[-2]) if len(vix_hist) > 1 else current_vix
            change = current_vix - previous_close
            change_percent = (change / previous_close) * 100 if previous_close \!= 0 else 0
            
            # Determine volatility regime
            if current_vix < 15:
                regime = "Low Volatility"
                context = "Compressed premiums, favor credit strategies"
            elif current_vix < 25:
                regime = "Normal Volatility"  
                context = "Balanced environment, multiple strategies viable"
            elif current_vix < 35:
                regime = "High Volatility"
                context = "Elevated premiums, consider selling strategies"
            else:
                regime = "Extreme Volatility"
                context = "Crisis mode, defensive positioning recommended"
            
            # Calculate historical percentile (simplified)
            vix_52w = yf.download("^VIX", period="1y", interval="1d", progress=False)
            if not vix_52w.empty:
                historical_percentile = (vix_52w['Close'] <= current_vix).mean() * 100
            else:
                historical_percentile = 50.0
            
            return VIXData(
                current=current_vix,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                context=context,
                regime=regime,
                historical_percentile=historical_percentile
            )
            
        except Exception as e:
            logger.error(f"Error fetching VIX data: {e}")
            # Return fallback data with error indication
            return VIXData(
                current=16.5,
                previous_close=16.0,
                change=0.5,
                change_percent=3.1,
                context="VIX data temporarily unavailable",
                regime="Unknown",
                historical_percentile=50.0
            )
    
    async def get_market_snapshot(self) -> MarketSnapshot:
        """Get comprehensive market snapshot."""
        try:
            # Get SPY data
            spy_hist = yf.download("SPY", period="2d", interval="1d", progress=False)
            spy_price = float(spy_hist['Close'].iloc[-1])
            spy_prev = float(spy_hist['Close'].iloc[-2]) if len(spy_hist) > 1 else spy_price
            spy_change = spy_price - spy_prev
            spy_change_percent = (spy_change / spy_prev) * 100 if spy_prev \!= 0 else 0
            
            # Get VIX data
            vix_data = await self.get_vix_data()
            
            # Determine market session
            session = self.get_current_market_session()
            
            return MarketSnapshot(
                spy_price=spy_price,
                spy_change=spy_change,
                spy_change_percent=spy_change_percent,
                vix_data=vix_data,
                session=session,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error creating market snapshot: {e}")
            raise
    
    def get_current_market_session(self) -> MarketSession:
        """Determine current market session based on ET time."""
        now = datetime.utcnow()
        et_hour = (now.hour - 5) % 24  # EST offset (simplified)
        
        if 4 <= et_hour < 9:
            return MarketSession.PRE_MARKET
        elif 9 <= et_hour < 16:
            return MarketSession.REGULAR_HOURS
        elif 16 <= et_hour < 20:
            return MarketSession.AFTER_HOURS
        else:
            return MarketSession.CLOSED
    
    async def generate_premarket_tweet(self) -> str:
        """Generate pre-market intelligence tweet."""
        try:
            snapshot = await self.get_market_snapshot()
            
            # Get earnings data (simplified)
            earnings_text = await self.get_earnings_summary()
            
            # Generate tweet content
            tweet = f"""🌅 PRE-MARKET INTEL

📊 SPY: ${snapshot.spy_price:.2f} ({snapshot.spy_change:+.2f}, {snapshot.spy_change_percent:+.1f}%)
⚡ VIX: {snapshot.vix_data.current:.1f} ({snapshot.vix_data.change:+.1f}, {snapshot.vix_data.change_percent:+.1f}%)
📈 Regime: {snapshot.vix_data.regime}

🎯 Strategy Focus: {snapshot.vix_data.context}

{earnings_text}

#PreMarket #OptionsTrading #VIX #SPY"""
            
            return tweet[:280]  # Twitter character limit
            
        except Exception as e:
            logger.error(f"Error generating pre-market tweet: {e}")
            return "🌅 PRE-MARKET INTEL\n\nMarket data updating... Check back soon\!\n\n#PreMarket #OptionsTrading"
    
    async def generate_market_open_tweet(self) -> str:
        """Generate market open tweet."""
        try:
            snapshot = await self.get_market_snapshot()
            
            tweet = f"""🔔 MARKET OPEN

📊 SPY: ${snapshot.spy_price:.2f} ({snapshot.spy_change_percent:+.1f}%)
⚡ VIX: {snapshot.vix_data.current:.1f} ({snapshot.vix_data.regime})
📍 {snapshot.vix_data.historical_percentile:.0f}th percentile (1Y)

🎯 Options Environment: {snapshot.vix_data.context}

#MarketOpen #OptionsTrading #TechnicalAnalysis"""
            
            return tweet[:280]
            
        except Exception as e:
            logger.error(f"Error generating market open tweet: {e}")
            return "🔔 MARKET OPEN\n\nTrading session begins\!\n\n#MarketOpen #OptionsTrading"
    
    async def generate_vix_monday_tweet(self) -> str:
        """Generate VIX Monday educational content."""
        try:
            vix_data = await self.get_vix_data()
            
            tweet = f"""📊 VIX MONDAY

Current VIX: {vix_data.current:.1f} ({vix_data.regime})
Historical Rank: {vix_data.historical_percentile:.0f}th percentile

💡 What this means:
{vix_data.context}

🎯 Strategy Implications:
{'Credit spreads shine in low vol' if vix_data.current < 20 else 'Consider protective strategies'}

#VIXMonday #VolatilityTrading #OptionsEducation"""
            
            return tweet[:280]
            
        except Exception as e:
            logger.error(f"Error generating VIX Monday tweet: {e}")
            return "📊 VIX MONDAY\n\nVolatility analysis and strategy insights\!\n\n#VIXMonday #OptionsEducation"
    
    async def get_earnings_summary(self) -> str:
        """Get today's earnings summary."""
        # Simplified earnings data - would integrate with real API
        earnings_companies = ["AAPL", "MSFT", "GOOGL"]  # Example
        if earnings_companies:
            return f"📈 Earnings Today: {', '.join(earnings_companies[:3])}"
        return "📈 Light earnings calendar today"
    
    def get_options_activity_summary(self, snapshot: MarketSnapshot) -> str:
        """Get options activity summary based on VIX."""
        if snapshot.vix_data.current < 15:
            return "Low vol environment favored sellers"
        elif snapshot.vix_data.current > 25:
            return "High vol created buying opportunities"
        else:
            return "Balanced flow, mixed strategies"

# Global service instance
_twitter_service = None

def get_twitter_service() -> TwitterAutomationService:
    """Get global Twitter automation service instance."""
    global _twitter_service
    if _twitter_service is None:
        _twitter_service = TwitterAutomationService()
    return _twitter_service
EOF < /dev/null
