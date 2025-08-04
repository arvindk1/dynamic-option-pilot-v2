"""
Market Commentary Service - Generate real-time market commentary
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from utils.universe_loader import get_universe_loader

logger = logging.getLogger(__name__)


class MarketSession(Enum):
    PRE_MARKET = "pre_market"
    REGULAR_HOURS = "regular_hours"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


class MarketCommentaryService:
    def __init__(self):
        self.universe_loader = get_universe_loader()
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = timedelta(minutes=30)  # Cache for 30 minutes

    def get_current_market_session(self) -> MarketSession:
        """Determine current market session based on ET time."""
        now = datetime.utcnow()
        # Convert to ET (simplified - doesn't handle DST)
        et_hour = (now.hour - 5) % 24  # EST offset

        if 4 <= et_hour < 9:  # 4 AM - 9 AM ET
            return MarketSession.PRE_MARKET
        elif 9 <= et_hour < 16:  # 9 AM - 4 PM ET
            return MarketSession.REGULAR_HOURS
        elif 16 <= et_hour < 20:  # 4 PM - 8 PM ET
            return MarketSession.AFTER_HOURS
        else:
            return MarketSession.CLOSED

    def generate_earnings_preview(self) -> List[str]:
        """Generate earnings preview for TOP 20 stocks."""
        top20_stocks = self.universe_loader.get_top20_stocks()

        # Mock earnings calendar - in production, would fetch from real API
        potential_earnings = [
            {
                "symbol": "AAPL",
                "when": "After Market Close",
                "consensus": "Beat Expected",
            },
            {
                "symbol": "MSFT",
                "when": "Before Market Open",
                "consensus": "Mixed Expectations",
            },
            {
                "symbol": "GOOGL",
                "when": "After Market Close",
                "consensus": "Revenue Growth Focus",
            },
            {
                "symbol": "NVDA",
                "when": "After Market Close",
                "consensus": "AI Demand Strong",
            },
            {
                "symbol": "TSLA",
                "when": "After Market Close",
                "consensus": "Delivery Numbers Key",
            },
            {
                "symbol": "META",
                "when": "After Market Close",
                "consensus": "Metaverse Investment Impact",
            },
            {
                "symbol": "AMZN",
                "when": "After Market Close",
                "consensus": "Cloud Growth Critical",
            },
        ]

        # Randomly select 2-3 earnings for today
        selected_earnings = random.sample(
            potential_earnings, min(3, len(potential_earnings))
        )

        earnings_notes = []
        for earning in selected_earnings:
            if earning["symbol"] in top20_stocks:
                earnings_notes.append(
                    f"{earning['symbol']} reports {earning['when'].lower()} - {earning['consensus']}"
                )

        return earnings_notes

    def generate_session_specific_content(
        self, session: MarketSession
    ) -> Dict[str, Any]:
        """Generate content specific to current market session."""
        current_date = datetime.utcnow()

        if session == MarketSession.PRE_MARKET:
            return {
                "headline": "Pre-Market Analysis: Futures Point to Mixed Open",
                "market_overview": f"Pre-market trading on {current_date.strftime('%A, %B %d, %Y')} shows mixed signals ahead of regular trading hours. Futures indicate potential volatility as markets digest overnight developments.",
                "session_focus": "Pre-market movers and futures direction",
                "key_timing": "Market opens at 9:30 AM ET",
            }

        elif session == MarketSession.REGULAR_HOURS:
            return {
                "headline": "Intraday Market Update: Active Trading Session",
                "market_overview": f"Markets actively trading on {current_date.strftime('%A, %B %d, %Y')} with ongoing price discovery across sectors. Options flow and volume patterns providing real-time sentiment indicators.",
                "session_focus": "Live price action and options activity",
                "key_timing": "Regular trading hours in progress",
            }

        elif session == MarketSession.AFTER_HOURS:
            return {
                "headline": "After-Hours Wrap: Market Close Analysis",
                "market_overview": f"Markets closed for regular trading on {current_date.strftime('%A, %B %d, %Y')}. After-hours activity and earnings releases setting up tomorrow's themes.",
                "session_focus": "Earnings results and after-hours moves",
                "key_timing": "After-hours trading until 8:00 PM ET",
            }

        else:  # CLOSED
            return {
                "headline": "Market Closed: Preparing for Next Session",
                "market_overview": f"Markets are closed. Analysis of {current_date.strftime('%A, %B %d, %Y')} session complete. Preparing themes and levels for next trading day.",
                "session_focus": "Session review and next-day preparation",
                "key_timing": "Next market open at 9:30 AM ET",
            }

    def generate_dynamic_themes(self) -> List[str]:
        """Generate dynamic market themes based on current conditions."""
        session = self.get_current_market_session()

        base_themes = [
            "Technology sector maintaining leadership with AI developments",
            "Interest rate environment influencing financial sector rotation",
            "Energy sector responding to geopolitical developments",
            "Healthcare names showing consolidation patterns",
        ]

        # Add earnings-specific themes if during earnings season
        earnings_themes = self.generate_earnings_preview()
        if earnings_themes:
            base_themes.extend(
                [f"Earnings focus: {theme}" for theme in earnings_themes]
            )

        # Add session-specific themes
        if session == MarketSession.PRE_MARKET:
            base_themes.append("Pre-market indicators suggesting potential gap moves")
        elif session == MarketSession.REGULAR_HOURS:
            base_themes.append(
                "Intraday momentum shifts creating options opportunities"
            )
        elif session == MarketSession.AFTER_HOURS:
            base_themes.append(
                "After-hours earnings reactions setting up extended moves"
            )

        return base_themes[:6]  # Limit to 6 themes

    def get_real_time_commentary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get real-time market commentary with caching."""

        # Check cache validity
        if (
            not force_refresh
            and self._cache_timestamp
            and datetime.utcnow() - self._cache_timestamp < self._cache_duration
            and self._cache
        ):
            return self._cache

        # Generate fresh commentary
        current_date = datetime.utcnow()
        current_timestamp = current_date.isoformat() + "Z"
        session = self.get_current_market_session()
        session_content = self.generate_session_specific_content(session)

        commentary = {
            "date": current_date.strftime("%Y-%m-%d"),
            "display_date": current_date.strftime("%A, %B %d, %Y"),
            "timestamp": current_timestamp,
            "market_session": session.value,
            "data_state": "demo",  # Mark as demo until real data integration
            "warning": "🚨 DEMO MODE - Connect real market data for live commentary",
            # Dynamic content based on session
            "headline": session_content["headline"],
            "market_overview": session_content["market_overview"],
            # Dynamic themes including earnings
            "key_themes": self.generate_dynamic_themes(),
            # Session-specific technical outlook
            "technical_outlook": f"SPY trading patterns suggest {session_content['session_focus'].lower()}. Current session: {session_content['key_timing']}",
            # Volatility analysis
            "volatility_watch": f"VIX levels during {session.value.replace('_', ' ')} showing market sentiment. Watch for {session_content['session_focus'].lower()}.",
            # Trading implications based on session
            "trading_implications": self._get_session_trading_implications(session),
            # Dynamic levels (would be real in production)
            "levels_to_watch": {
                "support_levels": [6300.0, 6280.0, 6250.0],
                "resistance_levels": [6380.0, 6400.0, 6420.0],
                "key_moving_averages": {
                    "sma_20": 6340.5,
                    "sma_50": 6315.2,
                    "sma_200": 6190.8,
                },
            },
            # Dynamic risk factors
            "risk_factors": self._get_current_risk_factors(session),
            # TOP 20 stocks focus
            "top20_focus": self._get_top20_highlights(),
            # Earnings calendar
            "earnings_preview": self.generate_earnings_preview(),
            "last_updated": current_timestamp,
            "next_update": self._get_next_update_time(),
            "is_demo": True,
        }

        # Update cache
        self._cache = commentary
        self._cache_timestamp = current_date

        return commentary

    def _get_session_trading_implications(self, session: MarketSession) -> List[str]:
        """Get trading implications specific to market session."""
        implications = {
            MarketSession.PRE_MARKET: [
                "Watch for gap trades and early momentum",
                "Options premiums may be elevated due to overnight risk",
                "Volume likely lower until regular hours begin",
                "Key levels from overnight futures to watch",
            ],
            MarketSession.REGULAR_HOURS: [
                "Full liquidity available for options strategies",
                "Intraday momentum providing directional opportunities",
                "Credit spreads benefiting from time decay",
                "Watch for reversal patterns at key levels",
            ],
            MarketSession.AFTER_HOURS: [
                "Earnings reactions creating volatility opportunities",
                "Limited liquidity affecting bid-ask spreads",
                "After-hours moves setting up next day's themes",
                "Focus on stocks with significant news flow",
            ],
            MarketSession.CLOSED: [
                "Plan strategies for next trading session",
                "Review day's performance and adjust positions",
                "Prepare for overnight developments",
                "Analyze earnings calendar for upcoming sessions",
            ],
        }

        return implications.get(session, implications[MarketSession.REGULAR_HOURS])

    def _get_current_risk_factors(self, session: MarketSession) -> List[str]:
        """Get current risk factors based on session and conditions."""
        base_risks = [
            "Federal Reserve policy shifts affecting market sentiment",
            "Geopolitical developments impacting global markets",
            "Earnings season results influencing sector rotation",
        ]

        if session == MarketSession.PRE_MARKET:
            base_risks.append("Overnight developments creating gap risk")
        elif session == MarketSession.AFTER_HOURS:
            base_risks.append("Limited liquidity amplifying price moves")

        base_risks.append("Options expiration flows may cause temporary volatility")

        return base_risks

    def _get_top20_highlights(self) -> List[str]:
        """Get highlights for TOP 20 stocks."""
        top20 = self.universe_loader.get_top20_stocks()

        # Generate some highlights (would be real analysis in production)
        highlights = []
        if "AAPL" in top20:
            highlights.append("AAPL showing relative strength in tech sector")
        if "NVDA" in top20:
            highlights.append("NVDA maintaining AI-driven momentum")
        if "TSLA" in top20:
            highlights.append("TSLA volatility creating options opportunities")

        return highlights[:3]  # Limit to 3 highlights

    def _get_next_update_time(self) -> str:
        """Calculate next scheduled update time."""
        now = datetime.utcnow()
        session = self.get_current_market_session()

        # Define update times (in ET, converted to UTC)
        if session == MarketSession.PRE_MARKET:
            # Next update at market open (9:30 AM ET = 2:30 PM UTC)
            next_update = now.replace(hour=14, minute=30, second=0, microsecond=0)
            if next_update <= now:
                next_update += timedelta(days=1)
        elif session == MarketSession.REGULAR_HOURS:
            # Next update at market close (4:30 PM ET = 9:30 PM UTC)
            next_update = now.replace(hour=21, minute=30, second=0, microsecond=0)
            if next_update <= now:
                next_update += timedelta(days=1)
        else:
            # Next update at pre-market (9:00 AM ET = 2:00 PM UTC)
            next_update = now.replace(hour=14, minute=0, second=0, microsecond=0)
            if next_update <= now:
                next_update += timedelta(days=1)

        return next_update.isoformat() + "Z"


# Global instance
_market_commentary_service = None


def get_market_commentary_service() -> MarketCommentaryService:
    """Get global market commentary service instance."""
    global _market_commentary_service
    if _market_commentary_service is None:
        _market_commentary_service = MarketCommentaryService()
    return _market_commentary_service
