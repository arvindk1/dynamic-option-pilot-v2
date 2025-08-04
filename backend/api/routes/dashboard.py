import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get dashboard metrics - simplified version for v2.0"""
    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z"

        # TODO: Check if real broker API is available
        # broker_connected = await check_broker_connection()
        broker_connected = False  # For now, no broker connected

        if broker_connected:
            # Would return real broker data here
            pass
        else:
            # Return demo data with clear state indicators
            return {
                "data_state": "demo",
                "warning": "🚨 DEMO MODE - Connect broker for live trading data",
                "demo_notice": "This is simulated data for development purposes",
                # Demo account data - clearly marked
                "account_balance": 100490.00,
                "cash": 45234.50,
                "buying_power": 180980.00,
                "account_status": "DEMO_ACTIVE",
                "account_id": "DEMO_ACCOUNT_12345",
                "margin_used": 55255.50,
                "options_level": "Level 4 (Demo)",
                # Demo trading statistics
                "total_pnl": 8490.00,
                "pnl_percentage": 9.24,
                "today_pnl": 485.32,
                "win_rate": 68.5,
                "total_trades": 47,
                "winning_trades": 32,
                "sharpe_ratio": 1.34,
                "max_drawdown": 0.04,
                "positions_open": 5,
                # Market data indicators
                "vix": 18.5,  # VIX volatility index
                "iv_rank": 0.45,  # IV rank as decimal (45th percentile)
                "last_updated": current_timestamp,
                "is_demo": True,
            }

    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting dashboard metrics: {str(e)}"
        )


@router.get("/performance")
async def get_performance_history(days: int = 30) -> Dict[str, Any]:
    """Get performance history for charts"""
    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z"

        # TODO: Check if real broker API is available
        broker_connected = False  # For now, no broker connected

        if broker_connected:
            # Would return real performance data here
            pass
        else:
            # Generate consistent demo performance data
            from datetime import timedelta

            now = datetime.utcnow()
            data = []

            # Use a seed for consistent demo data
            import random

            random.seed(42)  # Consistent seed for reproducible demo data

            base_value = 92000  # Starting value 30 days ago
            cumulative_pnl = 0

            for i in range(days):
                date = now - timedelta(days=days - i - 1)
                # Generate realistic but consistent daily changes
                daily_change = random.uniform(-800, 1200) * (
                    0.7 + 0.3 * random.random()
                )
                cumulative_pnl += daily_change

                data.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "daily_pnl": round(daily_change, 2),
                        "cumulative_pnl": round(cumulative_pnl, 2),
                        "account_value": round(base_value + cumulative_pnl, 2),
                    }
                )

            return {
                "data_state": "demo",
                "warning": "🚨 DEMO MODE - Connect broker for live performance data",
                "demo_notice": "This is simulated performance data for development purposes",
                "start_date": (now - timedelta(days=days)).isoformat(),
                "end_date": now.isoformat(),
                "data": data,
                "is_demo": True,
                "last_updated": current_timestamp,
            }

    except Exception as e:
        logger.error(f"Error getting performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
