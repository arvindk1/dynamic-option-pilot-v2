import logging
from fastapi import APIRouter
from core.orchestrator.plugin_registry import get_plugin_registry

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_positions(sync: bool = False):
    """Get current positions."""
    plugin_registry = get_plugin_registry()
    try:
        # Get Alpaca provider instance
        alpaca_provider = (
            plugin_registry.get_plugin("alpaca_provider") if plugin_registry else None
        )

        if not alpaca_provider:
            logger.warning("Alpaca provider not available, returning empty positions")
            return []

        # Fetch positions from Alpaca
        positions = await alpaca_provider.get_positions()
        logger.info(f"Retrieved {len(positions)} positions from Alpaca")
        return positions

    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return []


@router.post("/sync")
async def sync_positions():
    """Sync positions with broker."""
    plugin_registry = get_plugin_registry()
    try:
        # Get Alpaca provider instance
        alpaca_provider = (
            plugin_registry.get_plugin("alpaca_provider") if plugin_registry else None
        )

        if not alpaca_provider:
            return {
                "status": "error",
                "message": "Alpaca provider not available",
                "sync_results": {
                    "synced_positions": 0,
                    "new_positions": 0,
                    "updated_positions": 0,
                },
            }

        # Fetch fresh positions from Alpaca
        positions = await alpaca_provider.get_positions()

        return {
            "status": "success",
            "message": f"Successfully synced {len(positions)} positions from Alpaca",
            "sync_results": {
                "synced_positions": len(positions),
                "new_positions": len(positions),  # For now, treat all as new
                "updated_positions": 0,
            },
        }

    except Exception as e:
        logger.error(f"Error syncing positions: {e}")
        return {
            "status": "error",
            "message": f"Failed to sync positions: {str(e)}",
            "sync_results": {
                "synced_positions": 0,
                "new_positions": 0,
                "updated_positions": 0,
            },
        }


@router.post("/close/{position_id}")
async def close_position(position_id: str, exit_price: float = 0.0):
    """Close a position."""
    return {
        "status": "success",
        "message": f"Demo mode: Position {position_id} closed at ${exit_price}",
        "cancelled_orders": [],
        "cancelled_count": 0,
    }
