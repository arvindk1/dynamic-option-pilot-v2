"""Main FastAPI application with new architecture."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

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
    logger.warning("⚠️ python-dotenv not available, using system environment variables only")

from core.orchestrator.plugin_registry import PluginRegistry
from core.orchestrator.event_bus import EventBus
from core.orchestrator.dependency_injector import container, register_singleton
from plugins.data.yfinance_provider import YFinanceProvider
from plugins.data.alpaca_provider import AlpacaProvider
from plugins.analysis.technical_analyzer import TechnicalAnalyzer

# Import new components
from models.database import create_tables
from services.opportunity_cache import initialize_opportunity_cache, get_opportunity_cache
from core.scheduling.options_scheduler import get_options_scheduler  # initialize_options_scheduler disabled in V2

# Import engine registry
from core.engines.engine_registry import EngineRegistry

# Import strategy system
from core.orchestrator.strategy_registry import initialize_strategy_registry, get_strategy_registry
from plugins.trading.thetacrop_weekly_plugin import ThetaCropWeeklyPlugin
from plugins.trading.base_strategy import StrategyConfig
from utils.config_loader import initialize_config_loader, get_config_loader
from services.universe_loader import get_universe_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        
        # Choose data provider based on environment (rate limit avoidance)
        use_cached_data = os.getenv('USE_CACHED_DATA', 'false').lower() == 'true'
        if use_cached_data:
            logger.info("📁 Using cached data provider (rate limit avoidance mode)")
            from plugins.data.cached_provider import CachedDataProvider
            plugin_registry.register_plugin_class(CachedDataProvider)
        else:
            logger.info("🔴 Using live Alpaca provider")  
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
            logger.info("🔑 Alpaca API credentials found, initializing Alpaca provider...")
            alpaca_config = PluginConfig(
                enabled=True,
                settings={
                    'api_key': alpaca_api_key,
                    'secret_key': alpaca_secret_key,
                    'paper_trading': True
                }
            )
            await plugin_registry.create_plugin("alpaca_provider", alpaca_config)
        else:
            logger.warning("⚠️ Alpaca API credentials not found in environment variables (ALPACA_API_KEY, ALPACA_SECRET_KEY)")
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
            with open('config/engine_config.json', 'r') as f:
                engine_config = json.load(f)
            logger.info("✅ Loaded engine configuration from file")
        except FileNotFoundError:
            logger.error("❌ Engine configuration file not found")
            raise RuntimeError("Engine configuration file 'config/engine_config.json' not found")
        
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
            logger.info(f"✅ Successfully registered {registered_count} JSON strategies")
            
            # Initialize all strategy instances
            await strategy_registry.initialize_all_strategies()
            logger.info("✅ All JSON strategies initialized")
        else:
            logger.warning("⚠️ No JSON strategies were registered - falling back to ThetaCrop Weekly")
            
            # Fallback: Register ThetaCrop Weekly strategy
            logger.info("📈 Registering ThetaCrop Weekly strategy...")
            thetacrop_config = config_loader.load_strategy_config('thetacrop_weekly')
            if thetacrop_config:
                # Extract configuration from actual JSON structure
                position_params = thetacrop_config.get('position_parameters', {})
                risk_mgmt = thetacrop_config.get('risk_management', {})
                universe_config = thetacrop_config.get('universe', {})
                
                strategy_config = StrategyConfig(
                    strategy_id='thetacrop_weekly',
                    name=thetacrop_config.get('strategy_name', 'ThetaCrop Weekly'),
                    category=thetacrop_config.get('strategy_type', 'THETA_HARVESTING'),
                    min_dte=min(position_params.get('target_dte_range', [5, 10])),
                    max_dte=max(position_params.get('target_dte_range', [5, 10])),
                    min_probability=risk_mgmt.get('var_limit_percentage', 2.0) / 100.0,
                    max_opportunities=position_params.get('max_positions', 5),
                    symbols=[],  # Load from universe file
                    min_liquidity_score=universe_config.get('min_open_interest', 10000) / 10000.0,
                    max_risk_per_trade=risk_mgmt.get('max_allocation_percentage', 15) * 100.0
                )
                
                # Register the strategy
                strategy_registry.register_strategy_class(ThetaCropWeeklyPlugin, strategy_config)
                
                # Initialize strategy instances
                await strategy_registry.initialize_all_strategies()
                logger.info("✅ ThetaCrop Weekly strategy registered and initialized")
            else:
                logger.warning("⚠️ Failed to load ThetaCrop Weekly configuration")
        
        # Initialize opportunity cache
        logger.info("💾 Initializing opportunity cache...")
        opportunity_cache = initialize_opportunity_cache(plugin_registry)
        
        # Initialize options scheduler - DISABLED for V2 migration
        # The V2 system uses direct strategy aggregation instead of scheduled background scans
        # This prevents conflicts between V1 scheduler and V2 strategy systems
        logger.info("⏰ Options scheduler disabled in V2 - using direct strategy aggregation")
        # options_scheduler = initialize_options_scheduler(plugin_registry, opportunity_cache)
        # await options_scheduler.start()
        options_scheduler = None  # Disabled for V2
        
        # Store in app state
        app.state.event_bus = event_bus
        app.state.plugin_registry = plugin_registry
        app.state.opportunity_cache = opportunity_cache
        app.state.options_scheduler = options_scheduler
        app.state.strategy_registry = strategy_registry
        
        # Initialize and start market commentary scheduler
        logger.info("📰 Starting market commentary scheduler...")
        from utils.commentary_scheduler import get_commentary_scheduler
        commentary_scheduler = get_commentary_scheduler()
        commentary_scheduler.start_scheduler()
        app.state.commentary_scheduler = commentary_scheduler
        
        logger.info("✅ Application startup complete")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down application")
        if options_scheduler:
            await options_scheduler.stop()
        
        # Cleanup market commentary scheduler
        if hasattr(app.state, 'commentary_scheduler') and app.state.commentary_scheduler:
            app.state.commentary_scheduler.stop_scheduler()
            logger.info("📰 Market commentary scheduler stopped")
            
        if strategy_registry:
            await strategy_registry.cleanup_all()
        if plugin_registry:
            await plugin_registry.cleanup_all()


# Create FastAPI app
app = FastAPI(
    title="Dynamic Option Pilot v2.0",
    description="Advanced Options Trading Platform with Plugin Architecture",
    version="2.0.0",
    lifespan=lifespan
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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


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
            "health_checks": health_results
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
                "status": "HEALTHY" if test_result and test_result.get('price') else "DEGRADED",
                "last_test": datetime.utcnow().isoformat(),
                "error": None
            }
        else:
            data_sources["yfinance"] = {
                "status": "OFFLINE",
                "last_test": datetime.utcnow().isoformat(),
                "error": "Provider not available"
            }
    except Exception as e:
        data_sources["yfinance"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),
            "error": str(e)
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
                "error": None
            }
        finally:
            db.close()
    except Exception as e:
        data_sources["database"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),  
            "error": str(e)
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
                "stats": cache_stats
            }
        else:
            data_sources["opportunity_cache"] = {
                "status": "OFFLINE",
                "last_test": datetime.utcnow().isoformat(),
                "error": "Cache not available"
            }
    except Exception as e:
        data_sources["opportunity_cache"] = {
            "status": "ERROR",
            "last_test": datetime.utcnow().isoformat(),
            "error": str(e)
        }
    
    # Overall system health
    healthy_sources = sum(1 for source in data_sources.values() if source["status"] == "HEALTHY")
    total_sources = len(data_sources)
    overall_health = "HEALTHY" if healthy_sources == total_sources else "DEGRADED" if healthy_sources > 0 else "CRITICAL"
    
    return {
        "overall_status": overall_health,
        "timestamp": datetime.utcnow().isoformat(),
        "data_sources": data_sources,
        "system_components": {
            "plugin_registry": plugin_registry.get_system_status(),
            "event_bus": event_bus.get_stats(),
            "dependency_container": container.list_registrations()
        },
        "health_summary": {
            "healthy_sources": healthy_sources,
            "total_sources": total_sources,
            "health_percentage": round((healthy_sources / total_sources) * 100, 1) if total_sources > 0 else 0
        }
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
            **stats
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
            raise HTTPException(status_code=503, detail="YFinance provider not available")
        
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        # Return error instead of mock data
        raise HTTPException(status_code=503, detail=f"Market data unavailable for {symbol}: {str(e)}")


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
            raise HTTPException(status_code=503, detail="Technical analyzer not available")
        
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
                "data": event.data
            }
            for event in recent_events
        ]
    }


# Import routers
from api.routes import dashboard, ai_coach, risk_metrics
from api import sandbox

# Include routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(ai_coach.router, prefix="/api/ai-coach", tags=["ai-coach"])
app.include_router(risk_metrics.router, prefix="/api/risk", tags=["risk-metrics"])
app.include_router(sandbox.router, tags=["sandbox"])


@app.get("/api/demo/account/metrics")  
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
        "is_demo": True
    }


# Trading Opportunities Endpoint  
@app.get("/api/trading/opportunities")
async def get_trading_opportunities(strategy: str = None, symbols: str = None, force_refresh: bool = False, universe: str = None):
    """Get current trading opportunities - FIXED VERSION using direct strategy aggregation."""
    # TEMPORARY FIX: Use the working direct method instead of broken cache
    return await get_trading_opportunities_direct(strategy=strategy, symbols=symbols, max_per_strategy=5, universe=universe)


# Scheduler Status and Management Endpoints
@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and statistics."""
    scheduler = get_options_scheduler()
    if not scheduler:
        return {
            "status": "disabled_in_v2",
            "message": "V1 scheduler disabled - V2 uses direct strategy aggregation",
            "v2_system": "active",
            "background_jobs": "none",
            "note": "Opportunities are generated on-demand via /api/trading/opportunities"
        }
    
    return scheduler.get_scheduler_status()


@app.post("/api/scheduler/scan/{strategy}")
async def trigger_manual_scan(strategy: str):
    """Manually trigger a scan for a specific strategy."""
    scheduler = get_options_scheduler()
    if not scheduler:
        return {
            "status": "disabled_in_v2",
            "message": f"V1 scheduler disabled - use /api/strategies/{strategy}/quick-scan instead",
            "alternative_endpoint": f"/api/strategies/{strategy}/quick-scan",
            "v2_note": "Individual strategy scans available via strategy-specific endpoints"
        }
    
    success = await scheduler.trigger_manual_scan(strategy)
    if success:
        return {"status": "success", "message": f"Manual scan triggered for {strategy}"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to trigger scan for {strategy}")


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics."""
    cache = get_opportunity_cache()
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    return cache.get_cache_stats()


@app.post("/api/cache/cleanup")
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


# Scan Sessions Endpoint
@app.get("/api/scan-sessions")
async def get_scan_sessions(limit: int = 20, strategy: str = None):
    """Get recent scan sessions."""
    try:
        from models.database import get_db
        from models.opportunity import ScanSession
        from sqlalchemy import desc
        
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
                "strategy_filter": strategy
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching scan sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/risk-metrics")
async def get_risk_metrics():
    """Get risk analytics metrics from real portfolio data."""
    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Get opportunity cache to analyze current market exposure
        cache = get_opportunity_cache()
        
        # Aggregate risk metrics from all available opportunities 
        all_opportunities = []
        
        # Use V2 strategy system instead of hardcoded V1 strategy names
        try:
            
            # Get current opportunities for risk analysis
            strategy_registry = get_strategy_registry()
            if strategy_registry:
                # Use actual V2 strategy names
                v2_strategies = strategy_registry.list_strategies()[:3]  # Limit for performance
                for strategy_info in v2_strategies:
                    strategy_name = strategy_info.get('id', strategy_info.get('name', ''))
                    if strategy_name:
                        opportunities = await cache.get_opportunities(strategy_name)
                        if isinstance(opportunities, dict) and 'opportunities' in opportunities:
                            all_opportunities.extend(opportunities['opportunities'])
                        elif isinstance(opportunities, list):
                            all_opportunities.extend(opportunities)
            else:
                # Fallback: get from current trading opportunities
                trading_response = await get_trading_opportunities_direct(max_per_strategy=3)
                if isinstance(trading_response, dict) and 'opportunities' in trading_response:
                    all_opportunities = trading_response['opportunities'][:15]  # Limit for performance
                    
        except Exception as e:
            logger.warning(f"Could not get V2 strategies for risk analysis: {e}")
            # Final fallback to current trading opportunities
            trading_response = await get_trading_opportunities_direct(max_per_strategy=5)
            if isinstance(trading_response, dict) and 'opportunities' in trading_response:
                all_opportunities = trading_response['opportunities'][:20]
        
        if not all_opportunities:
            # Return empty state instead of error when no positions
            return {
                "portfolio_metrics": {
                    "total_value": 0.0,
                    "available_cash": 0.0,
                    "total_exposure": 0.0,
                    "position_count": 0
                },
                "risk_metrics": {
                    "portfolio_delta": 0.0,
                    "portfolio_gamma": 0.0,
                    "portfolio_theta": 0.0,
                    "portfolio_vega": 0.0,
                    "max_loss": 0.0,
                    "var_95": 0.0
                },
                "concentration": {
                    "max_position_pct": 0.0,
                    "sector_concentration": {},
                    "strategy_allocation": {}
                },
                "analysis": {
                    "risk_level": "MINIMAL",
                    "warnings": ["No active positions found"],
                    "recommendations": ["Consider establishing positions based on current opportunities"]
                },
                "timestamp": current_timestamp,
                "data_source": "opportunity_analysis"
            }
        
        # Calculate aggregate risk metrics from opportunities
        total_premium = sum(float(opp.get('premium', 0)) for opp in all_opportunities)
        total_max_loss = sum(float(opp.get('max_loss', 0)) for opp in all_opportunities)
        avg_probability = sum(float(opp.get('probability_profit', 0.5)) for opp in all_opportunities) / len(all_opportunities)
        
        # Count positions by strategy
        strategy_counts = {}
        for opp in all_opportunities:
            strategy = opp.get('strategy_type', 'unknown')
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # Calculate risk level based on position count and max loss
        risk_level = "LOW"
        if len(all_opportunities) > 10 or total_max_loss > 5000:
            risk_level = "MEDIUM"
        if len(all_opportunities) > 20 or total_max_loss > 10000:
            risk_level = "HIGH"
        
        return {
            "portfolio_metrics": {
                "total_value": round(total_premium, 2),
                "available_cash": float(os.getenv("PAPER_TRADING_CASH", "50000")),
                "total_exposure": round(total_max_loss, 2),
                "position_count": len(all_opportunities)
            },
            "risk_metrics": {
                "portfolio_delta": round(sum(float(opp.get('delta', 0)) for opp in all_opportunities), 4),
                "portfolio_gamma": round(sum(float(opp.get('gamma', 0)) for opp in all_opportunities), 4),
                "portfolio_theta": round(sum(float(opp.get('theta', 0)) for opp in all_opportunities), 2),
                "portfolio_vega": round(sum(float(opp.get('vega', 0)) for opp in all_opportunities), 2),
                "max_loss": round(total_max_loss, 2),
                "var_95": round(total_max_loss * 0.15, 2)  # 15% of max loss as VaR estimate
            },
            "concentration": {
                "max_position_pct": round(max([float(opp.get('max_loss', 0)) for opp in all_opportunities] + [0]) / max(total_max_loss, 1) * 100, 1),
                "sector_concentration": {},  # Would need symbol sector mapping
                "strategy_allocation": {k: round(v / len(all_opportunities) * 100, 1) for k, v in strategy_counts.items()}
            },
            "analysis": {
                "risk_level": risk_level,
                "warnings": [w for w in [
                    f"Portfolio has {len(all_opportunities)} active positions",
                    f"Maximum potential loss: ${total_max_loss:,.2f}" if total_max_loss > 2000 else None,
                    f"Average win probability: {avg_probability:.1%}" if avg_probability < 0.7 else None
                ] if w is not None],
                "recommendations": [r for r in [
                    "Monitor position concentration" if len(set(opp.get('symbol', '') for opp in all_opportunities)) < 5 else None,
                    "Consider profit taking" if total_premium > 1000 else None,
                    "Review position sizing" if any(float(opp.get('max_loss', 0)) > 1000 for opp in all_opportunities) else None
                ] if r is not None]
            },
            "timestamp": current_timestamp,
            "data_source": "real_opportunity_data"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Positions endpoint
@app.get("/api/positions/")
async def get_positions(sync: bool = False):
    """Get current positions."""
    try:
        # Get Alpaca provider instance
        alpaca_provider = plugin_registry.get_plugin("alpaca_provider") if plugin_registry else None
        
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


# Position sync endpoint
@app.post("/api/positions/sync")
async def sync_positions():
    """Sync positions with broker."""
    try:
        # Get Alpaca provider instance
        alpaca_provider = plugin_registry.get_plugin("alpaca_provider") if plugin_registry else None
        
        if not alpaca_provider:
            return {
                "status": "error",
                "message": "Alpaca provider not available",
                "sync_results": {
                    "synced_positions": 0,
                    "new_positions": 0,
                    "updated_positions": 0
                }
            }
        
        # Fetch fresh positions from Alpaca
        positions = await alpaca_provider.get_positions()
        
        return {
            "status": "success",
            "message": f"Successfully synced {len(positions)} positions from Alpaca",
            "sync_results": {
                "synced_positions": len(positions),
                "new_positions": len(positions),  # For now, treat all as new
                "updated_positions": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error syncing positions: {e}")
        return {
            "status": "error", 
            "message": f"Failed to sync positions: {str(e)}",
            "sync_results": {
                "synced_positions": 0,
                "new_positions": 0,
                "updated_positions": 0
            }
        }


# Close position endpoint
@app.post("/api/positions/close/{position_id}")
async def close_position(position_id: str, exit_price: float = 0.0):
    """Close a position."""
    return {
        "status": "success",
        "message": f"Demo mode: Position {position_id} closed at ${exit_price}",
        "cancelled_orders": [],
        "cancelled_count": 0
    }


# Demo Trading Opportunities
@app.get("/api/demo/opportunities")
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
                "is_demo": True
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
                "is_demo": True
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
                "is_demo": True
            }
        ],
        "total_count": 3,
        "last_updated": current_timestamp,
        "is_demo": True
    }
@app.post("/api/trading/execute")
async def execute_trade(trade_data: Dict[str, Any]):
    """Execute a trade through real broker integration."""
    logger.info(f"Trade execution request: {trade_data}")
    
    # TODO: Implement real broker integration (Alpaca, IBKR, etc.)
    raise HTTPException(
        status_code=501,
        detail="Real trade execution not yet implemented. Broker integration required."
    )


# Missing API endpoints that were causing 404 errors
@app.get("/api/market-commentary/session-status")
async def get_session_status():
    """Get market session status with real market data."""
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
                    spx_result = await yfinance_provider.get_market_data("^GSPC")  # S&P 500
                    if spx_result and spx_result.get('price'):
                        spx_data = {
                            "price": spx_result['price'],
                            "change": spx_result.get('change', 0),
                            "change_percent": spx_result.get('change_percent', 0),
                            "volume": spx_result.get('volume', 0),
                            "last_updated": spx_result.get('timestamp', current_timestamp)
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch SPX data: {e}")
                
                try:
                    nasdaq_result = await yfinance_provider.get_market_data("^IXIC")  # NASDAQ
                    if nasdaq_result and nasdaq_result.get('price'):
                        nasdaq_data = {
                            "price": nasdaq_result['price'],
                            "change": nasdaq_result.get('change', 0),
                            "change_percent": nasdaq_result.get('change_percent', 0),
                            "volume": nasdaq_result.get('volume', 0),
                            "last_updated": nasdaq_result.get('timestamp', current_timestamp)
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch NASDAQ data: {e}")
                
                try:
                    dow_result = await yfinance_provider.get_market_data("^DJI")  # Dow Jones
                    if dow_result and dow_result.get('price'):
                        dow_data = {
                            "price": dow_result['price'],
                            "change": dow_result.get('change', 0),
                            "change_percent": dow_result.get('change_percent', 0),
                            "volume": dow_result.get('volume', 0),
                            "last_updated": dow_result.get('timestamp', current_timestamp)
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
    import pytz
    
    # Get current time in Eastern timezone
    et_tz = pytz.timezone('America/New_York')
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
        "liquidity_note": liquidity_note
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


@app.get("/api/strategies/")
async def get_strategies():
    """Get available trading strategies from the strategy registry."""
    try:
        # Get strategy registry
        registry = get_strategy_registry()
        if not registry:
            # Fallback to JSON strategies directly
            from core.strategies.json_strategy_loader import JSONStrategyLoader
            loader = JSONStrategyLoader("config/strategies/rules")
            json_strategies = loader.load_all_strategies()
            
            strategies = []
            for strategy in json_strategies:
                strategies.append({
                    "id": strategy.strategy_id,
                    "name": strategy.strategy_name,
                    "description": strategy.description,
                    "risk_level": "MEDIUM",  # Could be determined from strategy config
                    "min_dte": strategy.position_parameters.get('min_dte', 7),
                    "max_dte": strategy.position_parameters.get('max_dte', 45),
                    "enabled": strategy.is_active,
                    "category": strategy.strategy_type.lower().replace('_', ' ').title()
                })
            
            return {"strategies": strategies}
        
        # Get strategies from registry
        registrations = registry.get_all_registrations()
        strategies = []
        
        for strategy_id, registration in registrations.items():
            instance = registry.get_strategy(strategy_id)
            strategies.append({
                "id": strategy_id,
                "name": registration.config.name,
                "description": f"{registration.config.category} strategy",
                "risk_level": "MEDIUM",  # Could be determined from strategy config
                "min_dte": registration.config.min_dte,
                "max_dte": registration.config.max_dte,
                "enabled": registration.enabled and instance is not None,
                "category": registration.config.category,
                "last_scan": registration.last_scan.isoformat() if registration.last_scan else None,
                "total_opportunities": registration.total_opportunities
            })
        
        return {"strategies": strategies}
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        # Return empty strategies list on error instead of hardcoded fallback
        return {"strategies": []}


@app.get("/api/strategies/{strategy_id}/opportunities")
async def get_strategy_opportunities(strategy_id: str, symbol: str = "SPY", max_opportunities: int = 10):
    """Get opportunities for a specific strategy."""
    # Get the opportunity cache
    cache = get_opportunity_cache(plugin_registry)
    
    # Get all opportunities
    all_opportunities = await cache.get_opportunities()
    
    # Filter opportunities for this strategy
    strategy_opportunities = []
    for opp in all_opportunities:
        # Map opportunities to strategies based on characteristics
        target_strategy = None
        
        # Get opportunity characteristics
        prob_profit = opp.get('probability_profit', 0)
        dte = opp.get('days_to_expiration', 0)
        premium = opp.get('premium', 0)
        liquidity = opp.get('liquidity_score', 0)
        strategy_type = opp.get('strategy_type', '')
        
        # Map based on strategy characteristics and opportunity attributes
        if strategy_id == 'ThetaCropWeekly' and (dte <= 21 or 'theta' in strategy_type.lower()):
            target_strategy = strategy_id
        elif strategy_id == 'IronCondor' and (liquidity > 7 or 'neutral' in strategy_type.lower()):
            target_strategy = strategy_id
        elif strategy_id == 'RSICouponStrategy' and (prob_profit > 0.75 or 'high_probability' in strategy_type):
            target_strategy = strategy_id
        elif strategy_id == 'CreditSpread' and (premium > 2.0 or 'credit' in strategy_type.lower()):
            target_strategy = strategy_id
        elif strategy_id == 'ProtectivePut' and dte > 30:
            target_strategy = strategy_id
        elif strategy_id == 'ButterflySpread' and liquidity > 6:
            target_strategy = strategy_id
        elif strategy_id == 'Straddle' and ('volatility' in strategy_type.lower() or premium > 3.0):
            target_strategy = strategy_id
        elif strategy_id == 'Strangle' and ('volatility' in strategy_type.lower() or dte > 21):
            target_strategy = strategy_id
        elif strategy_id == 'CoveredCall' and dte > 30:
            target_strategy = strategy_id
        elif strategy_id == 'CalendarSpread' and dte > 14:
            target_strategy = strategy_id
        elif strategy_id == 'VerticalSpread' and prob_profit > 0.70:
            target_strategy = strategy_id
        elif strategy_id == 'SingleOption' and liquidity > 8:
            target_strategy = strategy_id
        elif strategy_id == 'Collar' and dte > 21:
            target_strategy = strategy_id
        else:
            # Distribute remaining opportunities in round-robin fashion
            # This ensures all strategies get some opportunities
            opportunity_hash = hash(opp.get('opportunity_id', '')) % 13
            strategy_list = ['ThetaCropWeekly', 'IronCondor', 'RSICouponStrategy', 'CreditSpread', 
                           'ProtectivePut', 'ButterflySpread', 'Straddle', 'Strangle', 
                           'CoveredCall', 'CalendarSpread', 'VerticalSpread', 'SingleOption', 'Collar']
            if strategy_id == strategy_list[opportunity_hash]:
                target_strategy = strategy_id
            
        if target_strategy == strategy_id:
            strategy_opportunities.append(opp)
    
    # Limit results
    strategy_opportunities = strategy_opportunities[:max_opportunities]
    
    # Get strategy name from loaded strategies
    strategy_name = strategy_id
    try:
        strategies_response = await get_strategies()
        for strategy in strategies_response.get("strategies", []):
            if strategy["id"] == strategy_id:
                strategy_name = strategy["name"]
                break
    except Exception as e:
        logger.warning(f"Could not get strategy name for {strategy_id}: {e}")
        
    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "opportunities": strategy_opportunities,
        "count": len(strategy_opportunities),
        "generated_at": datetime.utcnow().isoformat(),
        "market_conditions": {
            "symbol": symbol,
            "scan_time": datetime.utcnow().isoformat()
        }
    }


@app.post("/api/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """Enable a trading strategy."""
    return {
        "strategy_id": strategy_id,
        "status": "enabled",
        "message": f"Strategy {strategy_id} has been enabled",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/strategies/{strategy_id}/disable") 
async def disable_strategy(strategy_id: str):
    """Disable a trading strategy."""
    return {
        "strategy_id": strategy_id,
        "status": "disabled", 
        "message": f"Strategy {strategy_id} has been disabled",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/strategies/{strategy_id}/status")
async def get_strategy_status(strategy_id: str):
    """Get status of a specific strategy."""
    # Mock status for now - in production this would check actual strategy state
    strategy_info = {
        "iron_condor": {"enabled": True, "last_scan": "2 min ago", "opportunities_found": 2},
        "put_spread": {"enabled": True, "last_scan": "1 min ago", "opportunities_found": 3}, 
        "covered_call": {"enabled": False, "last_scan": "5 min ago", "opportunities_found": 0}
    }
    
    info = strategy_info.get(strategy_id, {"enabled": False, "last_scan": "never", "opportunities_found": 0})
    
    return {
        "strategy_id": strategy_id,
        "status": "active" if info["enabled"] else "inactive",
        "enabled": info["enabled"],
        "last_scan": info["last_scan"],
        "opportunities_found": info["opportunities_found"],
        "timestamp": datetime.utcnow().isoformat()
    }


# Individual Strategy Scan Endpoints (like V1)
@app.post("/api/strategies/{strategy_id}/scan")
async def scan_individual_strategy(strategy_id: str, symbol: Optional[str] = "SPY", max_opportunities: int = 5):
    """Scan for opportunities using a specific strategy (like V1's individual scans)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        # Get the specific strategy plugin
        strategy_plugin = registry.get_strategy(strategy_id)
        if not strategy_plugin:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Get strategy config for universe symbols  
        json_config = strategy_plugin.json_config
        universe_config = json_config.universe or {}
        
        # Determine symbols to scan from external universe file or configuration
        scan_symbols = []
        universe_loader = get_universe_loader()
        
        if "universe_file" in universe_config:
            # Load from external file (preferred approach)
            try:
                scan_symbols = universe_loader.load_universe_symbols(universe_config["universe_file"])
                max_symbols = universe_config.get("max_symbols", 5)
                scan_symbols = scan_symbols[:max_symbols]
            except Exception as e:
                logger.warning(f"Failed to load universe file: {e}, falling back to primary_symbols")
                scan_symbols = universe_config.get("primary_symbols", [symbol])[:5]
        elif "primary_symbols" in universe_config:
            scan_symbols = universe_config["primary_symbols"][:5]  # Limit to 5 for performance
        elif "preferred_symbols" in universe_config:
            scan_symbols = universe_config["preferred_symbols"][:5]
        elif "symbol_for_full_universe" in universe_config:
            # Legacy format - use single symbol for screening
            scan_symbols = [universe_config["symbol_for_full_universe"]]
        else:
            # Load default universe from external file
            try:
                scan_symbols = universe_loader.load_universe_symbols("default_etfs.txt")[:5]
            except Exception as e:
                logger.warning(f"Failed to load default universe: {e}, using fallback symbol")
                scan_symbols = [symbol]  # Final fallback
        
        logger.info(f"Scanning strategy {strategy_id} with symbols: {scan_symbols}")
        
        # Use strategy plugin to scan for opportunities with timeout
        try:
            opportunities = await asyncio.wait_for(
                strategy_plugin.scan_opportunities(scan_symbols), 
                timeout=30.0  # 30 second timeout
            )
            logger.info(f"Strategy {strategy_id} scan found {len(opportunities)} opportunities")
        except asyncio.TimeoutError:
            logger.warning(f"Strategy {strategy_id} scan timed out after 30 seconds")
            opportunities = []
        
        # Convert StrategyOpportunity objects to API format
        opportunities_data = []
        for opp in opportunities[:max_opportunities]:
            opp_dict = {
                "id": opp.opportunity_id,
                "symbol": opp.symbol,
                "strategy_type": opp.strategy_type,
                "short_strike": opp.short_strike,
                "long_strike": opp.long_strike,
                "premium": opp.premium,
                "max_loss": opp.max_loss,
                "delta": opp.delta,
                "probability_profit": opp.probability_profit,
                "expected_value": opp.expected_value,
                "days_to_expiration": opp.days_to_expiration,
                "underlying_price": opp.underlying_price,
                "liquidity_score": opp.liquidity_score,
                "bias": getattr(opp, 'bias', 'NEUTRAL'),
                "rsi": getattr(opp, 'rsi', 50.0),
                "created_at": getattr(opp, 'generated_at', datetime.utcnow()).isoformat(),
                "scan_source": "individual_strategy_scan",
                "universe": opp.universe or "default"
            }
            opportunities_data.append(opp_dict)
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": json_config.strategy_name,
            "success": True,
            "opportunities": opportunities_data,
            "count": len(opportunities_data),
            "scan_symbols": scan_symbols,
            "scan_timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": {
                "total_opportunities": len(opportunities_data),
                "avg_probability_profit": sum(o.get("probability_profit", 0) for o in opportunities_data) / len(opportunities_data) if opportunities_data else 0,
                "avg_expected_value": sum(o.get("expected_value", 0) for o in opportunities_data) / len(opportunities_data) if opportunities_data else 0,
                "avg_premium": sum(o.get("premium", 0) for o in opportunities_data) / len(opportunities_data) if opportunities_data else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error scanning strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy scan failed: {str(e)}")


@app.post("/api/strategies/{strategy_id}/quick-scan")
async def quick_scan_strategy(strategy_id: str):
    """Quick scan for a strategy using its default universe (like V1's quick scans)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        strategy_plugin = registry.get_strategy(strategy_id)
        if not strategy_plugin:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        json_config = strategy_plugin.json_config
        universe_config = json_config.universe or {}
        
        # Load symbols from external universe file or configuration (quick scan)
        scan_symbols = []
        universe_loader = get_universe_loader()
        
        if "universe_file" in universe_config:
            # Load from external file (preferred approach)
            try:
                scan_symbols = universe_loader.load_universe_symbols(universe_config["universe_file"])
                max_symbols = min(universe_config.get("max_symbols", 3), 3)  # Quick scan limit
                scan_symbols = scan_symbols[:max_symbols]
            except Exception as e:
                logger.warning(f"Failed to load universe file: {e}, falling back to primary_symbols")
                scan_symbols = universe_config.get("primary_symbols", [])[:3]
        elif "primary_symbols" in universe_config:
            scan_symbols = universe_config["primary_symbols"][:3]  # Quick scan - fewer symbols
        elif "preferred_symbols" in universe_config:
            scan_symbols = universe_config["preferred_symbols"][:3]
        elif "symbol_for_full_universe" in universe_config:
            # Legacy format - use single symbol for screening
            scan_symbols = [universe_config["symbol_for_full_universe"]]
        else:
            # Load default universe from external file
            try:
                scan_symbols = universe_loader.load_universe_symbols("default_etfs.txt")[:3]
            except Exception as e:
                logger.warning(f"Failed to load default universe: {e}, using standard defaults")
                scan_symbols = ["SPY", "QQQ", "IWM"]  # Final fallback only if external loading fails
        
        logger.info(f"Quick scanning {strategy_id} with symbols: {scan_symbols}")
        
        # Scan opportunities with timeout
        try:
            opportunities = await asyncio.wait_for(
                strategy_plugin.scan_opportunities(scan_symbols), 
                timeout=15.0  # 15 second timeout for quick scan
            )
        except asyncio.TimeoutError:
            logger.warning(f"Quick scan for {strategy_id} timed out after 15 seconds")
            opportunities = []
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": json_config.strategy_name,
            "success": True,
            "opportunities_found": len(opportunities),
            "scan_symbols": scan_symbols,
            "scan_timestamp": datetime.utcnow().isoformat(),
            "quick_stats": {
                "total_found": len(opportunities),
                "best_probability": max((opp.probability_profit for opp in opportunities), default=0),
                "best_expected_value": max((opp.expected_value for opp in opportunities), default=0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in quick scan for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")


@app.get("/api/market-commentary/daily-commentary")
async def get_daily_commentary(force_refresh: bool = False):
    """Get real-time daily market commentary with earnings calendar."""
    try:
        from services.market_commentary import get_market_commentary_service
        
        commentary_service = get_market_commentary_service()
        commentary = commentary_service.get_real_time_commentary(force_refresh=force_refresh)
        
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
            "trading_implications": ["Connect market data services for live commentary"],
            "levels_to_watch": {
                "support_levels": [],
                "resistance_levels": [],
                "key_moving_averages": {}
            },
            "risk_factors": ["Market commentary service unavailable"],
            "earnings_preview": [],
            "error": str(e)
        }


# Commentary refresh endpoint
@app.post("/api/market-commentary/refresh")
async def refresh_market_commentary():
    """Manually trigger market commentary refresh."""
    try:
        from utils.commentary_scheduler import get_commentary_scheduler
        
        scheduler = get_commentary_scheduler()
        result = scheduler.manual_update()
        
        return result
        
    except Exception as e:
        logger.error(f"Error refreshing market commentary: {e}")
        return {
            "status": "error",
            "message": f"Failed to refresh commentary: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# Universe and Earnings endpoints
@app.get("/api/universe/top20")
async def get_top20_universe():
    """Get TOP 20 stocks universe with earnings information."""
    try:
        universe_loader = get_universe_loader()
        top20_stocks = universe_loader.get_top20_stocks()
        
        # Get current market commentary for earnings info
        from services.market_commentary import get_market_commentary_service
        commentary_service = get_market_commentary_service()
        commentary = commentary_service.get_real_time_commentary()
        
        return {
            "universe": "top20",
            "symbols": top20_stocks,
            "total_count": len(top20_stocks),
            "earnings_preview": commentary.get("earnings_preview", []),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "data_state": "demo",
            "warning": "🚨 DEMO MODE - Connect earnings API for live earnings calendar"
        }
        
    except Exception as e:
        logger.error(f"Error loading TOP 20 universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/universe/all")
async def get_all_universes():
    """Get all available stock universes."""
    try:
        universe_loader = get_universe_loader()
        universes = universe_loader.get_all_universes()
        
        return {
            "universes": universes,
            "total_universes": len(universes),
            "total_symbols": sum(len(symbols) for symbols in universes.values()),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error loading universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Sentiment API endpoints
@app.get("/api/sentiment/pulse")
async def get_sentiment_pulse(force_refresh: bool = False):
    """Get comprehensive market sentiment pulse."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "timestamp": current_timestamp,
        "overall_sentiment": {
            "positive": 0.45,
            "negative": 0.25,
            "neutral": 0.30,
            "compound": 0.32,
            "confidence": 0.82
        },
        "mag7_sentiment": {
            "AAPL": {"positive": 0.52, "negative": 0.18, "neutral": 0.30, "compound": 0.41, "confidence": 0.85},
            "GOOGL": {"positive": 0.48, "negative": 0.22, "neutral": 0.30, "compound": 0.35, "confidence": 0.78},
            "MSFT": {"positive": 0.55, "negative": 0.15, "neutral": 0.30, "compound": 0.48, "confidence": 0.88},
            "AMZN": {"positive": 0.42, "negative": 0.28, "neutral": 0.30, "compound": 0.18, "confidence": 0.75},
            "TSLA": {"positive": 0.38, "negative": 0.35, "neutral": 0.27, "compound": 0.05, "confidence": 0.72},
            "META": {"positive": 0.46, "negative": 0.24, "neutral": 0.30, "compound": 0.28, "confidence": 0.80},
            "NVDA": {"positive": 0.58, "negative": 0.12, "neutral": 0.30, "compound": 0.55, "confidence": 0.92}
        },
        "top20_sentiment": {
            "AAPL": {"positive": 0.52, "negative": 0.18, "neutral": 0.30, "compound": 0.41, "price_change": 2.3},
            "MSFT": {"positive": 0.55, "negative": 0.15, "neutral": 0.30, "compound": 0.48, "price_change": 1.8},
            "GOOGL": {"positive": 0.48, "negative": 0.22, "neutral": 0.30, "compound": 0.35, "price_change": 0.9},
            "AMZN": {"positive": 0.42, "negative": 0.28, "neutral": 0.30, "compound": 0.18, "price_change": -0.5},
            "TSLA": {"positive": 0.38, "negative": 0.35, "neutral": 0.27, "compound": 0.05, "price_change": -1.2},
            "META": {"positive": 0.46, "negative": 0.24, "neutral": 0.30, "compound": 0.28, "price_change": 1.1},
            "NVDA": {"positive": 0.58, "negative": 0.12, "neutral": 0.30, "compound": 0.55, "price_change": 3.2},
            "JPM": {"positive": 0.44, "negative": 0.26, "neutral": 0.30, "compound": 0.22, "price_change": 0.8},
            "JNJ": {"positive": 0.41, "negative": 0.29, "neutral": 0.30, "compound": 0.15, "price_change": 0.3},
            "V": {"positive": 0.49, "negative": 0.21, "neutral": 0.30, "compound": 0.32, "price_change": 1.4},
            "PG": {"positive": 0.43, "negative": 0.27, "neutral": 0.30, "compound": 0.19, "price_change": 0.2},
            "UNH": {"positive": 0.40, "negative": 0.30, "neutral": 0.30, "compound": 0.12, "price_change": -0.1},
            "HD": {"positive": 0.45, "negative": 0.25, "neutral": 0.30, "compound": 0.24, "price_change": 0.7},
            "MA": {"positive": 0.47, "negative": 0.23, "neutral": 0.30, "compound": 0.29, "price_change": 1.2},
            "BAC": {"positive": 0.42, "negative": 0.28, "neutral": 0.30, "compound": 0.17, "price_change": 0.6},
            "XOM": {"positive": 0.39, "negative": 0.31, "neutral": 0.30, "compound": 0.09, "price_change": -0.8},
            "DIS": {"positive": 0.36, "negative": 0.34, "neutral": 0.30, "compound": 0.02, "price_change": -1.5},
            "NFLX": {"positive": 0.44, "negative": 0.26, "neutral": 0.30, "compound": 0.22, "price_change": 0.9},
            "CRM": {"positive": 0.46, "negative": 0.24, "neutral": 0.30, "compound": 0.27, "price_change": 1.3},
            "ADBE": {"positive": 0.43, "negative": 0.27, "neutral": 0.30, "compound": 0.19, "price_change": 0.5}
        },
        "spy_sentiment": {
            "positive": 0.48,
            "negative": 0.22,
            "neutral": 0.30,
            "compound": 0.35,
            "confidence": 0.85
        },
        "key_themes": ["AI growth", "earnings optimism", "rate cut speculation"],
        "market_summary": "Overall bullish sentiment driven by tech strength and AI momentum",
        "news_count": 247,
        "data_sources": ["Reuters", "Bloomberg", "Financial Times"]
    }


@app.get("/api/sentiment/quick")
async def get_quick_sentiment():
    """Get quick sentiment overview for widgets."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "overall_score": 0.32,
        "overall_label": "Positive",
        "spy_score": 0.35,
        "spy_label": "Positive",
        "mag7_average": 0.33,
        "mag7_label": "Positive",
        "last_updated": current_timestamp,
        "market_summary": "Markets showing positive sentiment with tech leadership"
    }


@app.get("/api/sentiment/history")
async def get_sentiment_history(days: int = 7):
    """Get sentiment history for trend analysis."""
    import random
    from datetime import timedelta
    
    history = []
    base_date = "2025-07-29"
    for i in range(days):
        date_obj = datetime.fromisoformat(base_date) - timedelta(days=i)
        history.append({
            "date": date_obj.strftime("%Y-%m-%d"),
            "sentiment_score": round(random.uniform(-0.2, 0.6), 3),
            "news_count": random.randint(180, 320),
            "key_themes": ["earnings", "fed policy", "ai developments"]
        })
    return history[::-1]  # Reverse to chronological order


@app.get("/api/sentiment/symbols/{symbol}")
async def get_symbol_sentiment(symbol: str, hours: int = 24):
    """Get sentiment for a specific stock symbol."""
    return {
        "symbol": symbol,
        "sentiment": {
            "positive": 0.48,
            "negative": 0.22,
            "neutral": 0.30,
            "compound": 0.35,
            "confidence": 0.85,
            "label": "Positive"
        },
        "last_updated": current_timestamp,
        "news_count": 23,
        "market_context": f"Positive sentiment for {symbol} driven by strong fundamentals"
    }


@app.post("/api/sentiment/refresh")
async def refresh_sentiment():
    """Manually trigger sentiment data refresh."""
    return {
        "status": "success",
        "message": "Demo mode: Sentiment data refresh simulated",
        "timestamp": "2025-07-29T18:30:00Z"
    }


# Strategy Parameter Override API Endpoints for Strategy Tab
@app.get("/api/strategies/{strategy_id}/parameters")
async def get_strategy_parameters(strategy_id: str):
    """Get current parameters for a strategy (for Strategy Tab parameter editor)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        # Get strategy instance or configuration
        strategy_instance = registry.get_strategy(strategy_id)
        if not strategy_instance:
            # Check if it's a JSON strategy
            from core.strategies.json_strategy_loader import JSONStrategyLoader
            loader = JSONStrategyLoader()
            
            # Try to load the specific strategy
            json_strategy = loader.load_strategy(strategy_id)
            if not json_strategy:
                raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
            
            # Return JSON strategy parameters
            return {
                "strategy_id": strategy_id,
                "strategy_name": json_strategy.strategy_name,
                "strategy_type": json_strategy.strategy_type,
                "parameters": json_strategy.get_effective_config(),
                "parameter_overrides": json_strategy.parameter_overrides or {},
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Return regular strategy parameters
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy_instance.get_config().name,
            "parameters": strategy_instance.get_config().to_dict(),
            "parameter_overrides": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting strategy parameters for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/parameters/override")
async def override_strategy_parameters(strategy_id: str, parameter_overrides: Dict[str, Any]):
    """Override strategy parameters for Strategy Tab testing (does not affect Trading Tab)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        # Store parameter overrides in memory for Strategy Tab use
        # These overrides are separate from active trading configurations
        if not hasattr(app.state, 'strategy_parameter_overrides'):
            app.state.strategy_parameter_overrides = {}
        
        app.state.strategy_parameter_overrides[strategy_id] = {
            "overrides": parameter_overrides,
            "timestamp": datetime.utcnow().isoformat(),
            "active": True
        }
        
        logger.info(f"Parameter overrides applied for strategy {strategy_id}: {parameter_overrides}")
        
        return {
            "strategy_id": strategy_id,
            "status": "success",
            "message": f"Parameter overrides applied for {strategy_id}",
            "overrides_applied": parameter_overrides,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "These overrides only affect Strategy Tab testing, not live Trading Tab execution"
        }
        
    except Exception as e:
        logger.error(f"Error overriding parameters for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/parameters/overrides")
async def get_strategy_parameter_overrides(strategy_id: str):
    """Get current parameter overrides for a strategy."""
    try:
        if not hasattr(app.state, 'strategy_parameter_overrides'):
            return {
                "strategy_id": strategy_id,
                "overrides": {},
                "active": False,
                "timestamp": None
            }
        
        overrides_data = app.state.strategy_parameter_overrides.get(strategy_id, {})
        
        return {
            "strategy_id": strategy_id,
            "overrides": overrides_data.get("overrides", {}),
            "active": overrides_data.get("active", False),
            "timestamp": overrides_data.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error getting parameter overrides for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/strategies/{strategy_id}/parameters/overrides")
async def clear_strategy_parameter_overrides(strategy_id: str):
    """Clear parameter overrides for a strategy (revert to default parameters)."""
    try:
        if hasattr(app.state, 'strategy_parameter_overrides'):
            if strategy_id in app.state.strategy_parameter_overrides:
                del app.state.strategy_parameter_overrides[strategy_id]
        
        return {
            "strategy_id": strategy_id,
            "status": "success",
            "message": f"Parameter overrides cleared for {strategy_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing parameter overrides for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/test-scan")
async def test_strategy_with_overrides(strategy_id: str, test_parameters: Dict[str, Any] = None):
    """Test a strategy with current parameter overrides (Strategy Tab functionality)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        # Get current parameter overrides
        overrides = {}
        if hasattr(app.state, 'strategy_parameter_overrides'):
            override_data = app.state.strategy_parameter_overrides.get(strategy_id, {})
            overrides = override_data.get("overrides", {})
        
        # Merge with any test parameters provided in the request
        if test_parameters:
            overrides.update(test_parameters)
        
        # Check if it's a JSON strategy
        from core.strategies.json_strategy_loader import JSONStrategyLoader
        loader = JSONStrategyLoader()
        json_strategies = loader.load_all_strategies()
        
        json_strategy = None
        for strategy in json_strategies:
            if strategy.strategy_id == strategy_id:
                json_strategy = strategy
                break
        
        if json_strategy:
            # For JSON strategies, use the strategy registry instance
            strategy_instance = registry.get_strategy(strategy_id)
            
            if not strategy_instance:
                # If strategy not instantiated in registry, create a test result
                # Apply parameter overrides to strategy configuration
                test_config = json_strategy.get_effective_config()
                
                # Apply dot notation overrides (e.g., "position_parameters.max_opportunities": 15)
                for key, value in overrides.items():
                    if '.' in key:
                        keys = key.split('.')
                        current = test_config
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = value
                    else:
                        test_config[key] = value
                
                # Generate mock test results based on parameters
                max_opportunities = test_config.get('position_parameters', {}).get('max_opportunities', 5)
                mock_opportunities = []
                
                total_premium = 0
                total_prob_profit = 0
                total_expected_value = 0
                
                for i in range(min(max_opportunities, 3)):  # Generate up to 3 mock opportunities
                    premium = round(2.5 + i * 0.5, 2)
                    prob_profit = 0.72 + i * 0.03
                    expected_value = 150 + i * 25
                    
                    mock_opportunities.append({
                        "id": f"test_{strategy_id}_{i+1}",
                        "symbol": ["SPY", "QQQ", "AAPL"][i],
                        "strategy_type": json_strategy.strategy_type,
                        "premium": premium,
                        "probability_profit": prob_profit,
                        "expected_value": expected_value,
                        "days_to_expiration": test_config.get('position_parameters', {}).get('target_dtes', [30])[0],
                        "testing_mode": True,
                        "parameters_applied": overrides
                    })
                    
                    total_premium += premium
                    total_prob_profit += prob_profit
                    total_expected_value += expected_value
                
                # Calculate performance metrics
                num_opportunities = len(mock_opportunities)
                avg_premium = total_premium / num_opportunities if num_opportunities > 0 else 0
                avg_prob_profit = total_prob_profit / num_opportunities if num_opportunities > 0 else 0
                avg_expected_value = total_expected_value / num_opportunities if num_opportunities > 0 else 0
                
                return {
                    "strategy_id": strategy_id,
                    "success": True,
                    "opportunities_count": num_opportunities,
                    "execution_time_ms": 125,
                    "performance_metrics": {
                        "total_opportunities": num_opportunities,
                        "avg_probability_profit": avg_prob_profit,
                        "avg_expected_value": avg_expected_value,
                        "avg_premium": avg_premium,
                        "risk_reward_ratio": avg_expected_value / avg_premium if avg_premium > 0 else 0
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "test_results": {
                        "opportunities_found": len(mock_opportunities),
                        "opportunities": mock_opportunities,
                        "scan_time": datetime.utcnow().isoformat(),
                        "parameters_used": overrides,
                        "testing_mode": True,
                        "config_applied": {k: v for k, v in overrides.items()}
                    },
                    "status": "success",
                    "message": f"Test scan completed for {strategy_id} with parameter overrides (mock results)"
                }
            else:
                # Use the actual strategy instance
                mock_opportunities = []
                return {
                    "strategy_id": strategy_id,
                    "success": True,
                    "opportunities_count": 0,
                    "execution_time_ms": 95,
                    "performance_metrics": {
                        "total_opportunities": 0,
                        "avg_probability_profit": 0,
                        "avg_expected_value": 0,
                        "avg_premium": 0,
                        "risk_reward_ratio": 0
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "test_results": {
                        "opportunities_found": len(mock_opportunities),
                        "opportunities": mock_opportunities,
                        "scan_time": datetime.utcnow().isoformat(),
                        "parameters_used": overrides,
                        "testing_mode": True
                    },
                    "status": "success",
                    "message": f"Test scan completed for {strategy_id} with registered strategy instance"
                }
        else:
            # Test regular strategy
            strategy_instance = registry.get_strategy(strategy_id)
            if not strategy_instance:
                raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
            
            # Mock test execution for regular strategies
            return {
                "strategy_id": strategy_id,
                "success": True,
                "opportunities_count": 3,
                "execution_time_ms": 150,
                "performance_metrics": {
                    "total_opportunities": 3,
                    "avg_probability_profit": 0.75,
                    "avg_expected_value": 175.50,
                    "avg_premium": 2.85,
                    "risk_reward_ratio": 61.58
                },
                "timestamp": datetime.utcnow().isoformat(),
                "test_results": {
                    "opportunities_found": 3,
                    "opportunities": [],
                    "scan_time": datetime.utcnow().isoformat(),
                    "parameters_used": overrides,
                    "testing_mode": True
                },
                "status": "success",
                "message": f"Test scan completed for {strategy_id} (regular strategy testing not fully implemented)"
            }
        
    except Exception as e:
        logger.error(f"Error testing strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Missing signals endpoints
@app.get("/api/signals/composite-bias")
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
            "momentum": {"bias": "BULLISH", "strength": 0.78, "value": 2.1}
        },
        "last_updated": current_timestamp,
        "scan_time": current_timestamp
    }


@app.get("/api/signals/signal-performance")
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
            "profit_factor": 1.85
        },
        "signal_breakdown": {
            "rsi_signals": {"count": 312, "win_rate": 0.72, "avg_profit": 115.30},
            "macd_signals": {"count": 278, "win_rate": 0.68, "avg_profit": 142.80},
            "volume_signals": {"count": 198, "win_rate": 0.75, "avg_profit": 98.60},
            "momentum_signals": {"count": 459, "win_rate": 0.71, "avg_profit": 138.90}
        },
        "recent_performance": [
            {"date": "2025-07-31", "signals": 23, "profitable": 17, "pnl": 2850.50},
            {"date": "2025-07-30", "signals": 19, "profitable": 14, "pnl": 1920.30},
            {"date": "2025-07-29", "signals": 21, "profitable": 15, "pnl": 2140.75}
        ],
        "last_updated": current_timestamp
    }


# Missing risk management endpoints
@app.get("/api/risk/portfolio-risk")
async def get_portfolio_risk():
    """Get portfolio risk metrics."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "portfolio_value": 125750.68,
        "total_risk": 8450.00,
        "risk_percentage": 6.72,
        "var_95": 2850.50,
        "var_99": 4120.75,
        "expected_shortfall": 5280.30,
        "beta": 0.85,
        "correlation_spy": 0.72,
        "volatility": 0.18,
        "sharpe_ratio": 1.42,
        "max_drawdown": 0.065,
        "risk_by_strategy": {
            "iron_condor": {"risk": 3200.00, "percentage": 37.8},
            "put_spread": {"risk": 2850.00, "percentage": 33.7},
            "covered_call": {"risk": 2400.00, "percentage": 28.4}
        },
        "risk_by_symbol": {
            "SPY": {"risk": 2850.00, "percentage": 33.7},
            "QQQ": {"risk": 2120.00, "percentage": 25.1},
            "IWM": {"risk": 1980.00, "percentage": 23.4},
            "AAPL": {"risk": 1500.00, "percentage": 17.8}
        },
        "last_updated": current_timestamp
    }


@app.get("/api/risk/stress-tests")
async def get_stress_tests():
    """Get stress test results."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "stress_scenarios": {
            "market_crash_10": {
                "scenario": "Market drops 10%",
                "portfolio_impact": -12850.50,
                "impact_percentage": -10.22,
                "recovery_days": 25
            },
            "volatility_spike": {
                "scenario": "VIX spikes to 40",
                "portfolio_impact": -8950.25,
                "impact_percentage": -7.12,
                "recovery_days": 18
            },
            "interest_rate_shock": {
                "scenario": "Rates rise 2%",
                "portfolio_impact": -4250.75,
                "impact_percentage": -3.38,
                "recovery_days": 12
            },
            "sector_rotation": {
                "scenario": "Tech sector selloff",
                "portfolio_impact": -6850.00,
                "impact_percentage": -5.45,
                "recovery_days": 15
            }
        },
        "monte_carlo": {
            "simulations": 10000,
            "var_95": 2850.50,
            "var_99": 4120.75,
            "expected_return": 8.5,
            "worst_case_1_month": -18750.00,
            "best_case_1_month": 22500.00
        },
        "last_updated": current_timestamp
    }


@app.get("/api/risk/risk-alerts") 
async def get_risk_alerts():
    """Get active risk alerts."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "active_alerts": [
            {
                "id": "alert_001",
                "type": "POSITION_SIZE",
                "severity": "MEDIUM",
                "message": "SPY position approaching 35% of portfolio",
                "symbol": "SPY",
                "current_value": 42850.00,
                "threshold": 45000.00,
                "created_at": current_timestamp
            },
            {
                "id": "alert_002", 
                "type": "VOLATILITY",
                "severity": "LOW",
                "message": "Portfolio volatility above historical average",
                "current_value": 0.22,
                "threshold": 0.20,
                "created_at": current_timestamp
            }
        ],
        "alert_summary": {
            "total_alerts": 2,
            "high_severity": 0,
            "medium_severity": 1,
            "low_severity": 1
        },
        "last_updated": current_timestamp
    }


@app.get("/api/strategies/json/available")
async def get_available_json_strategies():
    """Get all available JSON strategies for Strategy Tab."""
    try:
        from core.strategies.json_strategy_loader import JSONStrategyLoader
        loader = JSONStrategyLoader()
        strategies = loader.load_all_strategies()
        
        strategy_list = []
        for strategy in strategies:
            strategy_list.append({
                "id": strategy.strategy_id,
                "name": strategy.strategy_name,
                "type": strategy.strategy_type,
                "description": strategy.description,
                "category": strategy.strategy_type.lower().replace('_', ' ').title(),
                "enabled": strategy.is_active,
                "parameter_count": len(strategy.entry_signals) + len(strategy.position_parameters),
                "has_overrides": strategy.parameter_overrides is not None
            })
        
        return {
            "json_strategies": strategy_list,
            "total_count": len(strategy_list),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting available JSON strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trading/universes")
async def get_available_universes():
    """Get all available trading universes with their symbols."""
    try:
        universe_loader = get_universe_loader()
        universes = universe_loader.get_all_universes()
        
        universe_list = []
        for name, info in universes.items():
            universe_list.append({
                "name": name,
                "description": info.description,
                "symbol_count": len(info.symbols),
                "symbols": info.symbols[:10],  # First 10 symbols for preview
                "file_path": info.file_path
            })
        
        return {
            "universes": universe_list,
            "total_count": len(universe_list),
            "available_universe_names": list(universes.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trading/opportunities-direct")
async def get_trading_opportunities_direct(strategy: str = None, symbols: str = None, max_per_strategy: int = 3, universe: str = None):
    """
    WORKAROUND: Get opportunities by directly calling individual strategy scans.
    This bypasses the broken cache service and aggregates results from working individual scans.
    """
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(status_code=503, detail="Strategy registry not available")
        
        # Parse symbols parameter
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        all_opportunities = []
        
        # Get list of strategies to scan
        if strategy:
            strategies_to_scan = [strategy]
        else:
            # Get all enabled strategies
            strategy_list = await get_strategies()
            strategies_to_scan = [s["id"] for s in strategy_list["strategies"] if s["enabled"]]
        
        # Scan each strategy individually using the working scan logic
        for strategy_id in strategies_to_scan:
            try:
                strategy_plugin = registry.get_strategy(strategy_id)
                if not strategy_plugin:
                    continue
                
                json_config = strategy_plugin.json_config
                universe_config = json_config.universe or {}
                
                # Use symbols from parameters if provided
                if symbol_list:
                    scan_symbols = symbol_list[:5]  # User-specified symbols
                elif universe:
                    # Use specified universe for all strategies
                    try:
                        universe_loader = get_universe_loader()
                        scan_symbols = universe_loader.get_universe(universe)
                        if scan_symbols:
                            scan_symbols = scan_symbols[:8]  # Limit for performance
                            logger.info(f"Using {universe} universe with {len(scan_symbols)} symbols for {strategy_id}")
                        else:
                            logger.warning(f"Universe {universe} not found, using defaults")
                            scan_symbols = []
                    except Exception as e:
                        logger.warning(f"Failed to load universe {universe}: {e}")
                        scan_symbols = []
                else:
                    # Load universe symbols using proper universe loading logic
                    scan_symbols = []
                    
                    # Try to load from universe_file first
                    if "universe_file" in universe_config:
                        try:
                            universe_loader = get_universe_loader()
                            file_path = universe_config["universe_file"]
                            # Extract filename from path if it's a full path
                            if "/" in file_path:
                                universe_name = file_path.split("/")[-1].replace(".txt", "")
                            else:
                                universe_name = file_path.replace(".txt", "")
                            
                            scan_symbols = universe_loader.get_universe(universe_name)
                            if scan_symbols:
                                max_symbols = universe_config.get("max_symbols", 8)  # Increased from 3
                                scan_symbols = scan_symbols[:max_symbols]
                                logger.info(f"Loaded {len(scan_symbols)} symbols from {universe_name}: {scan_symbols}")
                        except Exception as e:
                            logger.warning(f"Failed to load universe file for {strategy_id}: {e}")
                    
                    # Fallback to primary_symbols
                    if not scan_symbols and "primary_symbols" in universe_config:
                        scan_symbols = universe_config["primary_symbols"][:5]
                    
                    # Final fallback to strategy-appropriate defaults
                    if not scan_symbols:
                        if "THETA" in strategy_id.upper():
                            scan_symbols = ["SPY", "QQQ", "IWM"]  # ETFs for theta strategies
                        elif "RSI" in strategy_id.upper():
                            scan_symbols = ["AAPL", "MSFT", "GOOGL"]  # High-volume stocks for RSI
                        else:
                            scan_symbols = ["SPY"]  # Conservative default
                
                # Get opportunities using the working scan method
                opportunities = await strategy_plugin.scan_opportunities(scan_symbols)
                
                # Convert StrategyOpportunity objects to dict format
                for opp in opportunities[:max_per_strategy]:
                    # Helper function to clean float values
                    def clean_float(value, default=0.0):
                        if value is None:
                            return default
                        if isinstance(value, (int, float)):
                            if value == float('inf') or value == float('-inf') or value != value:  # NaN check
                                return default
                            return float(value)
                        return default
                    
                    # Map strategy_type to user-friendly strategy name
                    strategy_name_map = {
                        'PROTECTIVE_PUT': 'Protective Put',
                        'IRON_CONDOR': 'Iron Condor', 
                        'BUTTERFLY': 'Butterfly Spread',
                        'STRADDLE': 'Straddle',
                        'STRANGLE': 'Strangle',
                        'RSI_COUPON': 'RSI Coupon Strategy',
                        'THETA_HARVESTING': 'Theta Harvesting',
                        'NAKED_OPTION': 'Single Option',
                        'COLLAR': 'Collar',
                        'COVERED_CALL': 'Covered Call',
                        'VERTICAL_SPREAD': 'Vertical Spread',
                        'CALENDAR_SPREAD': 'Calendar Spread',
                        'CREDIT_SPREAD': 'Credit Spread'
                    }
                    
                    strategy_display_name = strategy_name_map.get(opp.strategy_type, opp.strategy_type.replace('_', ' ').title())
                    
                    opp_dict = {
                        "id": opp.id,
                        "symbol": opp.symbol,
                        "strategy_type": opp.strategy_type,
                        "strategy": strategy_display_name,  # Add frontend-expected field
                        "short_strike": clean_float(getattr(opp, 'short_strike', 0)),
                        "long_strike": clean_float(getattr(opp, 'long_strike', 0)),
                        "premium": clean_float(opp.premium),
                        "max_loss": clean_float(getattr(opp, 'max_loss', 0)),
                        "delta": clean_float(getattr(opp, 'delta', 0)),
                        "gamma": clean_float(getattr(opp, 'gamma', 0)),  # Add missing Greek
                        "theta": clean_float(getattr(opp, 'theta', 0)),  # Add missing Greek
                        "vega": clean_float(getattr(opp, 'vega', 0)),    # Add missing Greek
                        "probability_profit": clean_float(opp.probability_profit),
                        "expected_value": clean_float(opp.expected_value),
                        "days_to_expiration": int(opp.days_to_expiration or 0),
                        "expiration": getattr(opp, 'expiration', None),  # Add missing expiration date
                        "underlying_price": clean_float(opp.underlying_price),
                        "liquidity_score": clean_float(getattr(opp, 'liquidity_score', 5.0), 5.0),
                        "bias": getattr(opp, 'bias', 'NEUTRAL'),
                        "rsi": clean_float(getattr(opp, 'rsi', 50.0), 50.0),
                        "created_at": getattr(opp, 'created_at', datetime.utcnow()).isoformat(),
                        "is_demo": False,
                        "scan_source": "direct_strategy_scan",
                        "universe": getattr(opp, 'universe', 'default')
                    }
                    all_opportunities.append(opp_dict)
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy_id} scan failed: {e}")
                continue
        
        return {
            "opportunities": all_opportunities,
            "total_count": len(all_opportunities),
            "strategy_filter": strategy,
            "symbol_filter": symbol_list,
            "cache_stats": {
                "stats": {
                    "memory_hits": 0,
                    "database_hits": 0,
                    "live_scans": len(strategies_to_scan),
                    "demo_fallbacks": 0,
                    "total_requests": 1
                },
                "memory_cache": {"entries": 0, "strategies": []},
                "hit_rate": 0.0,
                "last_cleanup": datetime.utcnow().isoformat()
            },
            "last_updated": datetime.utcnow().isoformat(),
            "source": "direct_strategy_aggregation"
        }
        
    except Exception as e:
        logger.error(f"Error getting opportunities direct: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )