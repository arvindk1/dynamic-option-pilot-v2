"""Main FastAPI application with new architecture."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("📝 Loaded environment variables from .env file")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning(
        "⚠️ python-dotenv not available, using system environment variables only"
    )

# Import engine registry
from core.engines.engine_registry import EngineRegistry
from core.orchestrator.dependency_injector import container, register_singleton
from core.orchestrator.event_bus import EventBus
from core.orchestrator.plugin_registry import PluginRegistry

# Import strategy system
from core.orchestrator.strategy_registry import (
    get_strategy_registry,
    initialize_strategy_registry,
)
from core.scheduling.options_scheduler import (
    get_options_scheduler,
    initialize_options_scheduler,
)

# Import new components
from models.database import create_tables
from plugins.analysis.technical_analyzer import TechnicalAnalyzer
from plugins.data.alpaca_provider import AlpacaProvider
from plugins.data.yfinance_provider import YFinanceProvider
from plugins.trading.base_strategy import StrategyConfig
from plugins.trading.thetacrop_weekly_plugin import ThetaCropWeeklyPlugin
from services.opportunity_cache import (
    get_opportunity_cache,
    initialize_opportunity_cache,
)
from services.universe_loader import get_universe_loader
from utils.config_loader import get_config_loader, initialize_config_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
event_bus = None
plugin_registry = None
engine_registry = None
opportunity_cache = None
options_scheduler = None
strategy_registry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global event_bus, plugin_registry, engine_registry, opportunity_cache, options_scheduler, strategy_registry

    try:
        logger.info("🚀 Starting Dynamic Option Pilot v2.0")

        # Initialize database
        logger.info("📊 Initializing database...")
        create_tables()

        # Initialize event bus
        event_bus = EventBus()
        register_singleton(EventBus, event_bus)

        # Initialize plugin registry
        plugin_registry = PluginRegistry(event_bus)
        register_singleton(PluginRegistry, plugin_registry)

        # Register plugin classes
        plugin_registry.register_plugin_class(YFinanceProvider)
        plugin_registry.register_plugin_class(AlpacaProvider)
        plugin_registry.register_plugin_class(TechnicalAnalyzer)

        # Create plugin instances with configurations
        # Note: In production, these would come from config files
        await plugin_registry.create_plugin("yfinance_provider")
        await plugin_registry.create_plugin("technical_analyzer")

        # Create Alpaca provider with environment variable configuration
        from core.orchestrator.base_plugin import PluginConfig

        alpaca_api_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")

        if alpaca_api_key and alpaca_secret_key:
            logger.info(
                "🔑 Alpaca API credentials found, initializing Alpaca provider..."
            )
            alpaca_config = PluginConfig(
                enabled=True,
                settings={
                    "api_key": alpaca_api_key,
                    "secret_key": alpaca_secret_key,
                    "paper_trading": True,
                },
            )
            await plugin_registry.create_plugin("alpaca_provider", alpaca_config)
        else:
            logger.warning(
                "⚠️ Alpaca API credentials not found in environment variables (ALPACA_API_KEY, ALPACA_SECRET_KEY)"
            )
            logger.warning("🔧 Account data will use fallback/cached data only")

        # Initialize all plugins
        success = await plugin_registry.initialize_all()
        if not success:
            logger.warning("⚠️ Some plugins failed to initialize")

        # Initialize config loader
        logger.info("📝 Initializing configuration loader...")
        config_loader = initialize_config_loader()

        # Initialize engine registry
        logger.info("🔧 Initializing engine registry...")
        engine_registry = EngineRegistry(plugin_registry)

        # Load configuration for engine registry
        try:
            import json

            with open("config/engine_config.json", "r") as f:
                engine_config = json.load(f)
            logger.info("✅ Loaded engine configuration from file")
        except FileNotFoundError:
            logger.error("❌ Engine configuration file not found")
            raise RuntimeError(
                "Engine configuration file 'config/engine_config.json' not found"
            )

        await engine_registry.initialize(engine_config)
        register_singleton(EngineRegistry, engine_registry)

        # Initialize strategy registry
        logger.info("🎯 Initializing strategy registry...")
        strategy_registry = initialize_strategy_registry(plugin_registry)

        # Set engine registry for JSON strategies
        strategy_registry.set_engine_registry(engine_registry)

        # Initialize JSON strategy loader with environment-aware directory
        logger.info("📈 Initializing JSON strategy loader...")
        strategy_registry.initialize_json_strategy_loader()  # Let it auto-detect environment

        # Register all JSON strategies from rules directory
        logger.info("📊 Loading JSON strategies from config files...")
        registered_count = strategy_registry.register_json_strategies()

        if registered_count > 0:
            logger.info(
                f"✅ Successfully registered {registered_count} JSON strategies"
            )

            # Initialize all strategy instances
            await strategy_registry.initialize_all_strategies()
            logger.info("✅ All JSON strategies initialized")
        else:
            logger.warning(
                "⚠️ No JSON strategies were registered - falling back to ThetaCrop Weekly"
            )

            # Fallback: Register ThetaCrop Weekly strategy
            logger.info("📈 Registering ThetaCrop Weekly strategy...")
            thetacrop_config = config_loader.load_strategy_config("thetacrop_weekly")
            if thetacrop_config:
                # Extract configuration from actual JSON structure
                position_params = thetacrop_config.get("position_parameters", {})
                risk_mgmt = thetacrop_config.get("risk_management", {})
                universe_config = thetacrop_config.get("universe", {})

                strategy_config = StrategyConfig(
                    strategy_id="thetacrop_weekly",
                    name=thetacrop_config.get("strategy_name", "ThetaCrop Weekly"),
                    category=thetacrop_config.get("strategy_type", "THETA_HARVESTING"),
                    min_dte=min(position_params.get("target_dte_range", [5, 10])),
                    max_dte=max(position_params.get("target_dte_range", [5, 10])),
                    min_probability=risk_mgmt.get("var_limit_percentage", 2.0) / 100.0,
                    max_opportunities=position_params.get("max_positions", 5),
                    symbols=[],  # Load from universe file
                    min_liquidity_score=universe_config.get("min_open_interest", 10000)
                    / 10000.0,
                    max_risk_per_trade=risk_mgmt.get("max_allocation_percentage", 15)
                    * 100.0,
                )

                # Register the strategy
                strategy_registry.register_strategy_class(
                    ThetaCropWeeklyPlugin, strategy_config
                )

                # Initialize strategy instances
                await strategy_registry.initialize_all_strategies()
                logger.info("✅ ThetaCrop Weekly strategy registered and initialized")
            else:
                logger.warning("⚠️ Failed to load ThetaCrop Weekly configuration")

        # Initialize opportunity cache
        logger.info("💾 Initializing opportunity cache...")
        opportunity_cache = initialize_opportunity_cache(plugin_registry)

        # Initialize options scheduler
        logger.info("⏰ Initializing options scheduler...")
        options_scheduler = initialize_options_scheduler(
            plugin_registry, opportunity_cache
        )
        await options_scheduler.start()

        # Store in app state
        app.state.event_bus = event_bus
        app.state.plugin_registry = plugin_registry
        app.state.opportunity_cache = opportunity_cache
        app.state.options_scheduler = options_scheduler
        app.state.strategy_registry = strategy_registry

        logger.info("✅ Application startup complete")
        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down application")
        if options_scheduler:
            await options_scheduler.stop()
        if strategy_registry:
            await strategy_registry.cleanup_all()
        if plugin_registry:
            await plugin_registry.cleanup_all()


# Create FastAPI app
app = FastAPI(
    title="Dynamic Option Pilot v2.0",
    description="Advanced Options Trading Platform with Plugin Architecture",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
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


# System status endpoint
@app.get("/api/system/status")
async def system_status():
    """Get comprehensive system status including data source health."""
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
        from models.database import get_db

        db_gen = get_db()
        db = next(db_gen)
        try:
            # Simple query test
            from sqlalchemy import text

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


# Plugin management endpoints
@app.get("/plugins")
async def list_plugins():
    """List all registered plugins."""
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="Plugin registry not available")

    return plugin_registry.get_all_plugins()


@app.get("/plugins/{plugin_name}/status")
async def get_plugin_status(plugin_name: str):
    """Get status of a specific plugin."""
    if not plugin_registry:
        raise HTTPException(status_code=503, detail="Plugin registry not available")

    plugin = plugin_registry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return plugin.get_status()


@app.get("/engines/status")
async def get_engine_registry_status():
    """Get engine registry status and statistics."""
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


# Market data endpoints
@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol."""
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


@app.get("/options-chain/{symbol}")
async def get_options_chain(symbol: str, expiration: str):
    """Get options chain for a symbol."""
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


# Analysis endpoints
@app.post("/analysis/technical")
async def technical_analysis(data: Dict[str, Any]):
    """Perform technical analysis on provided data."""
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


# Event stream endpoint
@app.get("/events/stream")
async def event_stream():
    """Get real-time event stream (WebSocket would be better for production)."""
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


from api import sandbox
from api.routes import (
    dashboard,
    strategies,
    sentiment,
    risk,
    signals,
    market_data,
    universes,
    positions,
    scheduler,
    cache,
    system,
    demo,
)

# Include routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(universes.router, prefix="/api/universes", tags=["universes"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])
app.include_router(cache.router, prefix="/api/cache", tags=["cache"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(sandbox.router, tags=["sandbox"])

# Conditionally include demo router
if os.getenv("TRADING_ENVIRONMENT") != "production":
    app.include_router(demo.router, prefix="/api/demo", tags=["demo"])

# Trading Opportunities Endpoint
@app.get("/api/trading/opportunities")
async def get_trading_opportunities(
    strategy: str = None,
    symbols: str = None,
    force_refresh: bool = False,
    universe: str = None,
):
    """Get current trading opportunities from the cache."""
    cache = get_opportunity_cache()
    symbol_list = symbols.split(",") if symbols else None
    return await cache.get_opportunities(
        strategy=strategy, symbols=symbol_list, force_refresh=force_refresh
    )


# Scan Sessions Endpoint
@app.get("/api/scan-sessions")
async def get_scan_sessions(limit: int = 20, strategy: str = None):
    """Get recent scan sessions."""
    try:
        from sqlalchemy import desc

        from models.database import get_db
        from models.opportunity import ScanSession

        db_gen = get_db()
        db = next(db_gen)
        try:
            query = db.query(ScanSession)

            if strategy:
                query = query.filter(ScanSession.strategy == strategy)

            sessions = query.order_by(desc(ScanSession.started_at)).limit(limit).all()

            return {
                "sessions": [session.to_dict() for session in sessions],
                "total_count": len(sessions),
                "strategy_filter": strategy,
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error fetching scan sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trading/execute")
async def execute_trade(trade_data: Dict[str, Any]):
    """Execute a trade through real broker integration."""
    logger.info(f"Trade execution request: {trade_data}")

    # TODO: Implement real broker integration (Alpaca, IBKR, etc.)
    raise HTTPException(
        status_code=501,
        detail="Real trade execution not yet implemented. Broker integration required.",
    )




if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info",
    )
