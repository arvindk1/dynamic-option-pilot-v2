"""
Real-time VIX Integration Service
Professional volatility analysis for trading platform
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import yfinance as yf

logger = logging.getLogger(__name__)

class RealTimeVIXService:
    """Professional VIX data service with volatility regime analysis."""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
    def get_vix_data(self) -> Dict[str, Any]:
        """Get real-time VIX data with professional analysis."""
        
        try:
            # Fetch VIX data 
            vix_hist = yf.download("^VIX", period="5d", interval="1d", progress=False)
            
            if vix_hist.empty:
                return self._get_fallback_vix_data()
            
            # Fix deprecated pandas float() calls
            current_vix = float(vix_hist['Close'].iloc[-1].item())
            previous_close = float(vix_hist['Close'].iloc[-2].item()) if len(vix_hist) > 1 else current_vix
            daily_change = current_vix - previous_close
            change_percent = (daily_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Volatility regime analysis
            regime_data = self._analyze_volatility_regime(current_vix)
            
            return {
                "current": round(current_vix, 2),
                "daily_change": round(daily_change, 2),
                "change_percent": round(change_percent, 2),
                "regime": regime_data["regime"],
                "trading_implication": regime_data["trading_implication"],
                "professional_context": f"VIX {current_vix:.1f} ({change_percent:+.1f}%), {regime_data['regime'].lower()}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data_quality": "live"
            }
            
        except Exception as e:
            logger.error(f"Error fetching VIX data: {e}")
            return self._get_fallback_vix_data()
    
    def _analyze_volatility_regime(self, vix_level: float) -> Dict[str, str]:
        """Analyze volatility regime."""
        
        if vix_level < 15:
            return {
                "regime": "Low Volatility",
                "trading_implication": "Compressed premiums, credit strategies favored"
            }
        elif vix_level < 25:
            return {
                "regime": "Normal Volatility", 
                "trading_implication": "Balanced environment, multiple strategies viable"
            }
        else:
            return {
                "regime": "High Volatility",
                "trading_implication": "Elevated premiums, protective strategies recommended"
            }
    
    def _get_fallback_vix_data(self) -> Dict[str, Any]:
        """Return fallback VIX data when live data unavailable."""
        return {
            "current": 18.5,
            "daily_change": 0.5,
            "change_percent": 2.8,
            "regime": "Normal Volatility",
            "trading_implication": "Live data integration in progress",
            "professional_context": "VIX data temporarily unavailable",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data_quality": "fallback"
        }

# Global service instance
_vix_service = None

def get_vix_service() -> RealTimeVIXService:
    """Get global VIX service instance."""
    global _vix_service
    if _vix_service is None:
        _vix_service = RealTimeVIXService()
    return _vix_service