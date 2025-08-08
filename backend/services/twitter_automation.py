"""
Twitter Automation Service for Dynamic Options Pilot
Automated market intelligence posts for engagement and education
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

from services.market_commentary import MarketCommentaryService
from services.real_time_vix import get_vix_service
from utils.universe_loader import get_universe_loader

logger = logging.getLogger(__name__)

class PostType(Enum):
    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MID_DAY = "mid_day"
    MARKET_CLOSE = "market_close"
    AFTER_HOURS = "after_hours"
    WEEKEND_EDUCATION = "weekend_education"

class TwitterAutomationService:
    """Professional Twitter automation for market intelligence and engagement."""
    
    def __init__(self):
        self.market_service = MarketCommentaryService()
        self.vix_service = get_vix_service()
        self.universe_loader = get_universe_loader()
        
        # Twitter API configuration (to be set with real credentials)
        self.twitter_config = {
            "api_key": None,  # Set from environment
            "api_secret": None,
            "access_token": None,
            "access_token_secret": None
        }
        
        # Posting schedule (ET times)
        self.posting_schedule = {
            PostType.PRE_MARKET: "06:30",      # 6:30 AM ET
            PostType.MARKET_OPEN: "09:35",     # 9:35 AM ET (5 min after open)
            PostType.MID_DAY: "12:00",         # 12:00 PM ET
            PostType.MARKET_CLOSE: "16:05",    # 4:05 PM ET (5 min after close)
            PostType.AFTER_HOURS: "18:00",     # 6:00 PM ET
        }
    
    async def generate_premarket_tweet(self) -> str:
        """Generate pre-market intelligence tweet."""
        
        try:
            # Get real-time data
            vix_data = self.vix_service.get_vix_data()
            market_commentary = await self.market_service.generate_daily_commentary()
            
            # Format pre-market intelligence
            current_date = datetime.now().strftime("%b %d, %Y")
            
            # Build tweet components
            vix_current = vix_data.get("current_vix", 15.0)
            vix_change = vix_data.get("daily_change", 0.0)
            vix_direction = "↑" if vix_change > 0 else "↓" if vix_change < 0 else "→"
            
            # Key themes from market commentary
            themes = market_commentary.get("key_themes", [])[:2]  # Top 2 themes
            
            tweet = f"""🌅 PRE-MARKET INTEL | {current_date}

📊 Market Setup:
• VIX: {vix_current:.1f} ({vix_direction}{abs(vix_change):.1f}) - {vix_data.get('regime_description', 'Normal vol')}
• Key Focus: {themes[0] if themes else 'Mixed market signals'}

🎯 Today's Watch:
• {market_commentary.get('trading_implications', ['Market dynamics'])[0][:50] if market_commentary.get('trading_implications') else 'Monitor volatility patterns'}

#PreMarket #OptionsTrading #VIX #MarketIntel"""
            
            return tweet[:280]  # Twitter character limit
            
        except Exception as e:
            logger.error(f"Error generating pre-market tweet: {e}")
            return self._fallback_premarket_tweet()
    
    async def generate_market_open_tweet(self) -> str:
        """Generate market open reaction tweet."""
        
        try:
            vix_data = self.vix_service.get_vix_data()
            
            # Mock market data (in production, get real futures/indices)
            indices = {
                "SPX": {"price": 5285, "change": 0.8},
                "NDX": {"price": 18500, "change": 1.2},
                "VIX": {"price": vix_data.get("current_vix", 15.0), "change": vix_data.get("daily_change", 0.0)}
            }
            
            tweet = f"""🔔 MARKET OPEN | {datetime.now().strftime('%I:%M %p ET')}

📈 Opening Action:
• SPX: {indices['SPX']['price']} ({'+' if indices['SPX']['change'] > 0 else ''}{indices['SPX']['change']:.1f}%)
• NDX: {indices['NDX']['price']} ({'+' if indices['NDX']['change'] > 0 else ''}{indices['NDX']['change']:.1f}%)
• VIX: {indices['VIX']['price']:.1f} ({'+' if indices['VIX']['change'] > 0 else ''}{indices['VIX']['change']:.1f})

⚡ Early Read: {vix_data.get('trading_implication', 'Monitor initial momentum')}

#MarketOpen #LiveTrading #SPX #VIX"""
            
            return tweet[:280]
        
        except Exception as e:
            logger.error(f"Error generating market open tweet: {e}")
            return self._fallback_market_open_tweet()
    
    async def generate_market_close_tweet(self) -> str:
        """Generate market close wrap-up tweet."""
        
        try:
            vix_data = self.vix_service.get_vix_data()
            market_commentary = await self.market_service.generate_daily_commentary()
            
            # Performance summary (mock data - in production use real)
            performance = {
                "spx_change": "+1.2%",
                "top_sector": "Technology +2.1%",
                "laggard_sector": "Financials -0.8%"
            }
            
            tweet = f"""📝 MARKET WRAP | {datetime.now().strftime('%b %d, %Y')}

✅ Daily Summary:
• SPX: {performance['spx_change']} | {vix_data.get('regime_description', 'Normal volatility')}
• Leader: {performance['top_sector']}
• Laggard: {performance['laggard_sector']}

🔮 Tomorrow: {market_commentary.get('trading_implications', ['Monitor opening action'])[0][:60] if market_commentary.get('trading_implications') else 'Watch overnight developments'}

#MarketWrap #DailyRecap #OptionsTrading"""
            
            return tweet[:280]
        
        except Exception as e:
            logger.error(f"Error generating market close tweet: {e}")
            return self._fallback_market_close_tweet()
    
    async def generate_educational_tweet(self, topic: str = "volatility") -> str:
        """Generate educational content tweet."""
        
        educational_content = {
            "volatility": f"""📚 VIX EDUCATION MONDAY

🎯 Understanding VIX Levels:
• 0-12: Extremely low (complacency risk)
• 12-20: Normal range (balanced environment)
• 20-30: Elevated (caution warranted)  
• 30+: High stress (opportunity/danger)

Current VIX: {self.vix_service.get_vix_data().get('current_vix', 15.0):.1f}

💡 Trading Tip: High VIX = option premium rich, Low VIX = breakout setups

#VIXEducation #OptionsTrading #TradingTips""",

            "earnings": f"""📊 EARNINGS SEASON GUIDE

🎯 Key Metrics to Watch:
• EPS vs Consensus (surprise factor)
• Revenue growth (sustainability)
• Forward guidance (future outlook)
• Options IV crush (premium decay)

This Week: {len(self.universe_loader.get_top20_stocks())} major reports

💡 Strategy: Buy vol before, sell vol after (if IV elevated)

#EarningsTrading #OptionsStrategy #TradingEducation""",

            "options": f"""⚡ OPTIONS WEDNESDAY

🎯 Greeks Simplified:
• Delta: Price sensitivity (0.30 = $30 per $100 move)
• Theta: Time decay (-$10/day typical)
• Vega: Vol sensitivity ($5 per 1% IV change)
• Gamma: Delta acceleration

💡 Pro Tip: Monitor Greeks changes, not just P&L

#OptionsEducation #Greeks #TradingStrategy"""
        }
        
        return educational_content.get(topic, educational_content["volatility"])
    
    async def generate_weekend_recap(self) -> str:
        """Generate weekend market recap and week ahead preview."""
        
        tweet = f"""📈 WEEK AHEAD | {(datetime.now() + timedelta(days=1)).strftime('%b %d')}

🎯 Key Events:
• Economic Calendar: Fed speakers, jobless claims
• Earnings Focus: 15+ S&P 500 reports
• Technical Levels: SPX 5250 support, 5350 resistance

⚡ Volatility Setup: 
VIX {self.vix_service.get_vix_data().get('current_vix', 15.0):.1f} - {self.vix_service.get_vix_data().get('regime_description', 'balanced environment')}

#WeekAhead #TradingPreview #MarketOutlook"""
        
        return tweet[:280]
    
    def _fallback_premarket_tweet(self) -> str:
        """Fallback tweet if data fetch fails."""
        return f"""🌅 PRE-MARKET INTEL | {datetime.now().strftime('%b %d, %Y')}

📊 Market Setup: Monitoring pre-market action
🎯 Focus: Volatility patterns and sector rotation
⚡ Strategy: Wait for confirmation at open

#PreMarket #OptionsTrading #MarketIntel"""
    
    def _fallback_market_open_tweet(self) -> str:
        """Fallback market open tweet."""
        return f"""🔔 MARKET OPEN | {datetime.now().strftime('%I:%M %p ET')}

📈 Opening Action: Monitoring initial moves
⚡ Early Read: Watch volume confirmation
🎯 Focus: Key level breaks and sector leadership

#MarketOpen #LiveTrading"""
    
    def _fallback_market_close_tweet(self) -> str:
        """Fallback market close tweet.""" 
        return f"""📝 MARKET WRAP | {datetime.now().strftime('%b %d, %Y')}

✅ Daily Summary: Mixed market action
🔮 Tomorrow: Monitor overnight developments
⚡ Strategy: Prepare for next session

#MarketWrap #DailyRecap"""
    
    async def schedule_daily_posts(self) -> Dict[str, str]:
        """Generate all scheduled posts for the day."""
        
        posts = {}
        
        try:
            posts[PostType.PRE_MARKET.value] = await self.generate_premarket_tweet()
            posts[PostType.MARKET_OPEN.value] = await self.generate_market_open_tweet()
            posts[PostType.MARKET_CLOSE.value] = await self.generate_market_close_tweet()
            posts["weekend_recap"] = await self.generate_weekend_recap()
            
            # Educational content rotation
            day_of_week = datetime.now().weekday()
            educational_topics = ["volatility", "earnings", "options", "technical", "risk"]
            topic = educational_topics[day_of_week % len(educational_topics)]
            posts["educational"] = await self.generate_educational_tweet(topic)
            
        except Exception as e:
            logger.error(f"Error scheduling daily posts: {e}")
        
        return posts
    
    def get_posting_analytics(self) -> Dict[str, Any]:
        """Get analytics for Twitter posting performance."""
        
        # Mock analytics - in production, connect to Twitter Analytics API
        return {
            "followers_count": 1250,  # Would be real from Twitter API
            "daily_impressions": 15000,
            "engagement_rate": 0.08,
            "top_performing_hashtags": ["#OptionsTrading", "#VIX", "#MarketIntel"],
            "best_posting_times": ["06:30 ET", "16:05 ET", "12:00 ET"],
            "growth_rate": "+15% this month"
        }

# Singleton instance
_twitter_service = None

def get_twitter_service() -> TwitterAutomationService:
    """Get or create Twitter automation service instance."""
    global _twitter_service
    if _twitter_service is None:
        _twitter_service = TwitterAutomationService()
    return _twitter_service