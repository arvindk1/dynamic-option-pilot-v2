import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from core.orchestrator.plugin_registry import get_plugin_registry
from core.orchestrator.event_bus import get_event_bus
from core.engines.engine_registry import get_engine_registry
from models.database import get_db
from sqlalchemy import text

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    plugin_registry = get_plugin_registry()
    try:
        if not plugin_registry:
            return {"status": "starting", "plugins": {}}

        plugin_status = plugin_registry.get_system_status()
        health_results = await plugin_registry.health_check_all()

        return {
            "status": "healthy" if all(health_results.values()) else "degraded",
            "plugins": plugin_status,
            "health_checks": health_results,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/status")
async def system_status():
    """Get comprehensive system status including data source health."""
    plugin_registry = get_plugin_registry()
    event_bus = get_event_bus()
    if not plugin_registry or not event_bus:
        raise HTTPException(status_code=503, detail="System not ready")

    # Test data source connectivity
    data_sources = {}

    # Test YFinance provider
    try:
        yfinance_provider = plugin_registry.get_plugin("yfinance_provider")
        if yfinance_provider:
            # Quick test fetch
            test_result = await yfinance_provider.get_market_data("SPY")
            data_sources["yfinance"] = {
                "status": (
                    "HEALTHY"
                    if test_result and test_result.get("price")
                    else "DEGRADED"
                ),
                "last_test": datetime.utcnow().isoformat(),
                "error": None,
            }
        else:
            data_sources["yfinance"] = {
                "status": "OFFLINE",
                "last_test": datetime.utcnow().isoformat(),
                "error": "Provider not available",
            }
    except Exception as e:
        data_sources["yfinance"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),
            "error": str(e),
        }

    # Test database connectivity
    try:
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Simple query test
            db.execute(text("SELECT 1"))
            data_sources["database"] = {
                "status": "HEALTHY",
                "last_test": datetime.utcnow().isoformat(),
                "error": None,
            }
        finally:
            db.close()
    except Exception as e:
        data_sources["database"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),
            "error": str(e),
        }

    # Test opportunity cache
    from services.opportunity_cache import get_opportunity_cache
    try:
        cache = get_opportunity_cache()
        if cache:
            cache_stats = cache.get_cache_stats()
            data_sources["opportunity_cache"] = {
                "status": "HEALTHY",
                "last_test": datetime.utcnow().isoformat(),
                "error": None,
                "stats": cache_stats,
            }
        else:
            data_sources["opportunity_cache"] = {
                "status": "OFFLINE",
                "last_test": datetime.utcnow().isoformat(),
                "error": "Cache not available",
            }
    except Exception as e:
        data_sources["opportunity_cache"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),
            "error": str(e),
        }

    # Overall system health
    healthy_sources = sum(
        1 for source in data_sources.values() if source["status"] == "HEALTHY"
    )
    total_sources = len(data_sources)
    overall_health = (
        "HEALTHY"
        if healthy_sources == total_sources
        else "DEGRADED" if healthy_sources > 0 else "CRITICAL"
    )

    from core.orchestrator.dependency_injector import container
    return {
        "overall_status": overall_health,
        "timestamp": datetime.utcnow().isoformat(),
        "data_sources": data_sources,
        "system_components": {
            "plugin_registry": plugin_registry.get_system_status(),
            "event_bus": event_bus.get_stats(),
            "dependency_container": container.list_registrations(),
        },
        "health_summary": {
            "healthy_sources": healthy_sources,
            "total_sources": total_sources,
            "health_percentage": (
                round((healthy_sources / total_sources) * 100, 1)
                if total_sources > 0
                else 0
            ),
        },
    }


@router.get("/plugins")
async def list_plugins():
    """List all registered plugins."""
    plugin_registry = get_plugin_registry()
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="Plugin registry not available")

    return plugin_registry.get_all_plugins()


@router.get("/plugins/{plugin_name}/status")
async def get_plugin_status(plugin_name: str):
    """Get status of a specific plugin."""
    plugin_registry = get_plugin_registry()
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="Plugin registry not available")

    plugin = plugin_registry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return plugin.get_status()


@router.get("/engines/status")
async def get_engine_registry_status():
    """Get engine registry status and statistics."""
    engine_registry = get_engine_registry()
    if not engine_registry:
        raise HTTPException(status_code=503, detail="Engine registry not available")

    try:
        stats = engine_registry.get_provider_stats()
        return {
            "status": "healthy" if engine_registry._initialized else "initializing",
            "timestamp": datetime.utcnow().isoformat(),
            **stats,
        }
    except Exception as e:
        logger.error(f"Error getting engine registry status: {e}")
        raise HTTPException(status_code=500, detail=f"Engine registry error: {str(e)}")


@router.get("/events/stream")
async def event_stream():
    """Get real-time event stream (WebSocket would be better for production)."""
    event_bus = get_event_bus()
    if not event_bus:
        raise HTTPException(status_code=503, detail="Event bus not available")

    # Return recent events (in production, implement WebSocket)
    recent_events = event_bus.get_event_history(limit=50)

    return {
        "events": [
            {
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "data": event.data,
            }
            for event in recent_events
        ]
    }
