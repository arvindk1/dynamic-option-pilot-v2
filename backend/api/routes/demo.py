import logging
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/account/metrics")
async def get_demo_account_metrics():
    """Get demo account metrics with clear state indicators."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "data_state": "demo",
        "warning": "🚨 DEMO MODE - This is simulated account data",
        "demo_notice": "Connect broker for live trading data",
        # Demo account data - clearly marked
        "account_balance": 125750.68,
        "cash": 95234.50,
        "buying_power": 190469.00,
        "options_level": "Level 4 (Demo)",
        "account_status": "DEMO_ACTIVE",
        "account_id": "DEMO_ACCOUNT_12345",
        "total_pnl": 2575.68,
        "today_pnl": 485.32,
        "open_positions": 3,
        "margin_used": 4500,
        "win_rate": 72.5,
        "total_trades": 40,
        "sharpe_ratio": 1.42,
        "max_drawdown": 0.06,
        # Market data indicators
        "vix": 19.2,  # VIX volatility index
        "iv_rank": 0.52,  # IV rank as decimal (52nd percentile)
        "last_updated": current_timestamp,
        "is_demo": True,
    }

@router.get("/opportunities")
async def get_demo_opportunities():
    """Get demo trading opportunities with clear state indicators."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "data_state": "demo",
        "warning": "🚨 DEMO MODE - These are simulated trading opportunities",
        "demo_notice": "Connect live data sources for real opportunities",
        "opportunities": [
            {
                "id": "demo_opp_1",
                "symbol": "SPY",
                "short_strike": 615,
                "long_strike": 605,
                "premium": 2.85,
                "max_loss": 715,
                "delta": -0.12,
                "probability_profit": 0.78,
                "expected_value": 195.50,
                "days_to_expiration": 28,
                "underlying_price": 627.50,
                "liquidity_score": 9.2,
                "bias": "BULLISH",
                "rsi": 45.3,
                "is_demo": True,
            },
            {
                "id": "demo_opp_2",
                "symbol": "QQQ",
                "strike": 385,
                "premium": 3.20,
                "max_loss": 320,
                "delta": 0.35,
                "probability_profit": 0.58,
                "expected_value": 85.00,
                "days_to_expiration": 6,
                "underlying_price": 382.15,
                "liquidity_score": 8.8,
                "bias": "NEUTRAL",
                "rsi": 52.1,
                "is_demo": True,
            },
            {
                "id": "demo_opp_3",
                "symbol": "NVDA",
                "short_strike": 115,
                "premium": 2.75,
                "max_loss": 275,
                "delta": 0.32,
                "probability_profit": 0.65,
                "expected_value": 138.00,
                "days_to_expiration": 42,
                "underlying_price": 118.45,
                "liquidity_score": 9.5,
                "bias": "STRONG",
                "rsi": 28.5,
                "is_demo": True,
            },
        ],
        "total_count": 3,
        "last_updated": current_timestamp,
        "is_demo": True,
    }
