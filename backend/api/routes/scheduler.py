import logging
from fastapi import APIRouter, HTTPException
from core.scheduling.options_scheduler import get_options_scheduler

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status and statistics."""
    scheduler = get_options_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    return scheduler.get_scheduler_status()


@router.post("/scan/{strategy}")
async def trigger_manual_scan(strategy: str):
    """Manually trigger a scan for a specific strategy."""
    scheduler = get_options_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    success = await scheduler.trigger_manual_scan(strategy)
    if success:
        return {"status": "success", "message": f"Manual scan triggered for {strategy}"}
    else:
        raise HTTPException(
            status_code=400, detail=f"Failed to trigger scan for {strategy}"
        )
