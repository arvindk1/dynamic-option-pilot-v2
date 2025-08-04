import logging
from typing import Dict, Any
from datetime import datetime
import pytz
from fastapi import APIRouter, HTTPException

from core.orchestrator.plugin_registry import PluginRegistry
from services.market_commentary import get_market_commentary_service
from utils.commentary_scheduler import get_commentary_scheduler
from core.orchestrator.plugin_registry import get_plugin_registry

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol."""
    plugin_registry = get_plugin_registry()
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="System not ready")

    try:
        # Get YFinance provider (primary data source)
        yfinance_provider = plugin_registry.get_plugin("yfinance_provider")
        if yfinance_provider:
            data = await yfinance_provider.get_market_data(symbol)
            return data
        else:
            # No fallback data - return error state
            raise HTTPException(
                status_code=503, detail="YFinance provider not available"
            )

    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        # Return error instead of mock data
        raise HTTPException(
            status_code=503, detail=f"Market data unavailable for {symbol}: {str(e)}"
        )


@router.get("/options-chain/{symbol}")
async def get_options_chain(symbol: str, expiration: str):
    """Get options chain for a symbol."""
    plugin_registry = get_plugin_registry()
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="System not ready")

    try:
        yfinance_provider = plugin_registry.get_plugin("yfinance_provider")
        if not yfinance_provider:
            raise HTTPException(status_code=503, detail="Data provider not available")

        data = await yfinance_provider.get_options_chain(symbol, expiration=expiration)
        return data

    except Exception as e:
        logger.error(f"Error fetching options chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/technical")
async def technical_analysis(data: Dict[str, Any]):
    """Perform technical analysis on provided data."""
    plugin_registry = get_plugin_registry()
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="System not ready")

    try:
        technical_analyzer = plugin_registry.get_plugin("technical_analyzer")
        if not technical_analyzer:
            raise HTTPException(
                status_code=503, detail="Technical analyzer not available"
            )

        analysis_result = await technical_analyzer.analyze(data)
        return analysis_result

    except Exception as e:
        logger.error(f"Technical analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commentary/session-status")
async def get_session_status():
    """Get market session status with real market data."""
    plugin_registry = get_plugin_registry()
    current_timestamp = datetime.utcnow().isoformat() + "Z"

    # Try to get real market data from YFinance provider
    spx_data = None
    nasdaq_data = None
    dow_data = None
    data_source_error = None

    try:
        if plugin_registry:
            yfinance_provider = plugin_registry.get_plugin("yfinance_provider")
            if yfinance_provider:
                # Fetch real market data
                try:
                    spx_result = await yfinance_provider.get_market_data(
                        "^GSPC"
                    )  # S&P 500
                    if spx_result and spx_result.get("price"):
                        spx_data = {
                            "price": spx_result["price"],
                            "change": spx_result.get("change", 0),
                            "change_percent": spx_result.get("change_percent", 0),
                            "volume": spx_result.get("volume", 0),
                            "last_updated": spx_result.get(
                                "timestamp", current_timestamp
                            ),
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch SPX data: {e}")

                try:
                    nasdaq_result = await yfinance_provider.get_market_data(
                        "^IXIC"
                    )  # NASDAQ
                    if nasdaq_result and nasdaq_result.get("price"):
                        nasdaq_data = {
                            "price": nasdaq_result["price"],
                            "change": nasdaq_result.get("change", 0),
                            "change_percent": nasdaq_result.get("change_percent", 0),
                            "volume": nasdaq_result.get("volume", 0),
                            "last_updated": nasdaq_result.get(
                                "timestamp", current_timestamp
                            ),
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch NASDAQ data: {e}")

                try:
                    dow_result = await yfinance_provider.get_market_data(
                        "^DJI"
                    )  # Dow Jones
                    if dow_result and dow_result.get("price"):
                        dow_data = {
                            "price": dow_result["price"],
                            "change": dow_result.get("change", 0),
                            "change_percent": dow_result.get("change_percent", 0),
                            "volume": dow_result.get("volume", 0),
                            "last_updated": dow_result.get(
                                "timestamp", current_timestamp
                            ),
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch DOW data: {e}")
            else:
                data_source_error = "YFinance provider not available"
        else:
            data_source_error = "Plugin registry not initialized"
    except Exception as e:
        data_source_error = f"Market data service error: {str(e)}"
        logger.error(f"Error fetching market data: {e}")

    # If no real data available, return error state instead of mock data
    if not spx_data and not nasdaq_data and not dow_data:
        data_source_error = data_source_error or "All market data sources unavailable"

    # Determine current market session based on Eastern Time
    et_tz = pytz.timezone("America/New_York")
    current_et = datetime.now(et_tz)
    current_time = current_et.time()
    current_weekday = current_et.weekday()  # 0=Monday, 6=Sunday

    # Market hours: Monday-Friday 9:30 AM - 4:00 PM ET
    # Pre-market: 4:00 AM - 9:30 AM ET
    # After-hours: 4:00 PM - 8:00 PM ET
    # Closed: Weekends and outside all trading hours

    session_status = "CLOSED"
    session_name = "Market Closed"
    is_trading_hours = False
    volume_expectation = "LOW"
    liquidity_note = "Limited liquidity - market closed"

    # Only determine trading status on weekdays (Monday=0 to Friday=4)
    if current_weekday < 5:  # Monday through Friday
        from datetime import time

        if current_time >= time(9, 30) and current_time < time(16, 0):
            session_status = "REGULAR_HOURS"
            session_name = "Regular Trading Hours"
            is_trading_hours = True
            volume_expectation = "HIGH"
            liquidity_note = "Good liquidity during regular hours"
        elif current_time >= time(4, 0) and current_time < time(9, 30):
            session_status = "PRE_MARKET"
            session_name = "Pre-Market Session"
            is_trading_hours = False
            volume_expectation = "MODERATE"
            liquidity_note = "Reduced liquidity - pre-market hours"
        elif current_time >= time(16, 0) and current_time < time(20, 0):
            session_status = "AFTER_HOURS"
            session_name = "After-Hours Session"
            is_trading_hours = False
            volume_expectation = "LOW"
            liquidity_note = "Reduced liquidity - after-hours trading"

    # Calculate next market open
    next_market_open = current_et.replace(hour=9, minute=30, second=0, microsecond=0)
    if current_weekday >= 5 or (current_weekday < 5 and current_time >= time(16, 0)):
        # If it's weekend or after 4 PM on weekday, next open is next Monday 9:30 AM
        days_ahead = 7 - current_weekday if current_weekday >= 5 else 1
        if current_weekday == 4 and current_time >= time(16, 0):  # Friday after 4 PM
            days_ahead = 3  # Next Monday
        next_market_open = next_market_open + timedelta(days=days_ahead)
    elif current_time >= time(16, 0):
        # After 4 PM on weekday, next open is tomorrow
        next_market_open = next_market_open + timedelta(days=1)

    response = {
        "session_status": session_status,
        "session_name": session_name,
        "current_time_et": current_et.isoformat(),
        "next_market_open": next_market_open.isoformat(),
        "is_trading_hours": is_trading_hours,
        "volume_expectation": volume_expectation,
        "liquidity_note": liquidity_note,
    }

    # Only include data if real data is available
    if spx_data:
        response["spx_data"] = spx_data
    if nasdaq_data:
        response["nasdaq_data"] = nasdaq_data
    if dow_data:
        response["dow_data"] = dow_data

    # Include error information for debugging
    if data_source_error:
        response["data_source_status"] = "ERROR"
        response["data_source_error"] = data_source_error
        logger.warning(f"Market data unavailable: {data_source_error}")
    else:
        response["data_source_status"] = "OK"

    return response


@router.get("/commentary/daily-commentary")
async def get_daily_commentary(force_refresh: bool = False):
    """Get real-time daily market commentary with earnings calendar."""
    try:
        commentary_service = get_market_commentary_service()
        commentary = commentary_service.get_real_time_commentary(
            force_refresh=force_refresh
        )

        return commentary

    except Exception as e:
        logger.error(f"Error generating market commentary: {e}")

        # Fallback to basic commentary if service fails
        current_date = datetime.utcnow()
        current_timestamp = current_date.isoformat() + "Z"

        return {
            "date": current_date.strftime("%Y-%m-%d"),
            "display_date": current_date.strftime("%A, %B %d, %Y"),
            "timestamp": current_timestamp,
            "data_state": "error",
            "warning": "⚠️ Market commentary service unavailable",
            "headline": "Market Commentary Service Unavailable",
            "market_overview": f"Unable to generate real-time commentary for {current_date.strftime('%A, %B %d, %Y')}. Check market data connections.",
            "key_themes": ["Market commentary service offline"],
            "technical_outlook": "Technical analysis unavailable",
            "volatility_watch": "Volatility analysis unavailable",
            "trading_implications": [
                "Connect market data services for live commentary"
            ],
            "levels_to_watch": {
                "support_levels": [],
                "resistance_levels": [],
                "key_moving_averages": {},
            },
            "risk_factors": ["Market commentary service unavailable"],
            "earnings_preview": [],
            "error": str(e),
        }


@router.post("/commentary/refresh")
async def refresh_market_commentary():
    """Manually trigger market commentary refresh."""
    try:
        scheduler = get_commentary_scheduler()
        result = scheduler.manual_update()

        return result

    except Exception as e:
        logger.error(f"Error refreshing market commentary: {e}")
        return {
            "status": "error",
            "message": f"Failed to refresh commentary: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
