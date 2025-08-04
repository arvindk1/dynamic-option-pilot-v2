import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from services.universe_loader import get_universe_loader
from services.market_commentary import get_market_commentary_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/top20")
async def get_top20_universe():
    """Get TOP 20 stocks universe with earnings information."""
    try:
        universe_loader = get_universe_loader()
        top20_stocks = universe_loader.get_top20_stocks()

        # Get current market commentary for earnings info
        commentary_service = get_market_commentary_service()
        commentary = commentary_service.get_real_time_commentary()

        return {
            "universe": "top20",
            "symbols": top20_stocks,
            "total_count": len(top20_stocks),
            "earnings_preview": commentary.get("earnings_preview", []),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "data_state": "demo",
            "warning": "🚨 DEMO MODE - Connect earnings API for live earnings calendar",
        }

    except Exception as e:
        logger.error(f"Error loading TOP 20 universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_universes():
    """Get all available stock universes."""
    try:
        universe_loader = get_universe_loader()
        universes = universe_loader.get_all_universes()

        return {
            "universes": universes,
            "total_universes": len(universes),
            "total_symbols": sum(len(symbols) for symbols in universes.values()),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        logger.error(f"Error loading universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading")
async def get_available_trading_universes():
    """Get all available trading universes with their symbols."""
    try:
        universe_loader = get_universe_loader()
        universes = universe_loader.get_all_universes()

        universe_list = []
        for name, info in universes.items():
            universe_list.append(
                {
                    "name": name,
                    "description": info.description,
                    "symbol_count": len(info.symbols),
                    "symbols": info.symbols[:10],  # First 10 symbols for preview
                    "file_path": info.file_path,
                }
            )

        return {
            "universes": universe_list,
            "total_count": len(universe_list),
            "available_universe_names": list(universes.keys()),
        }

    except Exception as e:
        logger.error(f"Error getting universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
