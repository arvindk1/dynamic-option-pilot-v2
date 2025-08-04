import logging
from fastapi import APIRouter, HTTPException
from services.opportunity_cache import get_opportunity_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_cache_stats():
    """Get cache performance statistics."""
    cache = get_opportunity_cache()
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")

    return cache.get_cache_stats()


@router.post("/cleanup")
async def trigger_cache_cleanup():
    """Manually trigger cache cleanup."""
    cache = get_opportunity_cache()
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")

    try:
        await cache.cleanup_expired()
        return {"status": "success", "message": "Cache cleanup completed"}
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
