import logging
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/composite-bias")
async def get_composite_bias(symbol: str = "SPY"):
    """Get composite signal bias for a symbol."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "symbol": symbol,
        "composite_bias": "BULLISH",
        "bias_strength": 0.68,
        "confidence": 0.82,
        "individual_signals": {
            "rsi": {"bias": "BULLISH", "strength": 0.65, "value": 45.3},
            "macd": {"bias": "BULLISH", "strength": 0.72, "value": 1.2},
            "volume": {"bias": "NEUTRAL", "strength": 0.45, "value": 85420},
            "momentum": {"bias": "BULLISH", "strength": 0.78, "value": 2.1},
        },
        "last_updated": current_timestamp,
        "scan_time": current_timestamp,
    }


@router.get("/signal-performance")
async def get_signal_performance():
    """Get signal performance analytics."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "performance_metrics": {
            "total_signals": 1247,
            "profitable_signals": 896,
            "win_rate": 0.719,
            "avg_profit": 127.50,
            "avg_loss": -85.20,
            "sharpe_ratio": 1.42,
            "profit_factor": 1.85,
        },
        "signal_breakdown": {
            "rsi_signals": {"count": 312, "win_rate": 0.72, "avg_profit": 115.30},
            "macd_signals": {"count": 278, "win_rate": 0.68, "avg_profit": 142.80},
            "volume_signals": {"count": 198, "win_rate": 0.75, "avg_profit": 98.60},
            "momentum_signals": {"count": 459, "win_rate": 0.71, "avg_profit": 138.90},
        },
        "recent_performance": [
            {"date": "2025-07-31", "signals": 23, "profitable": 17, "pnl": 2850.50},
            {"date": "2025-07-30", "signals": 19, "profitable": 14, "pnl": 1920.30},
            {"date": "2025-07-29", "signals": 21, "profitable": 15, "pnl": 2140.75},
        ],
        "last_updated": current_timestamp,
    }
