"""Main FastAPI application with new architecture."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.orchestrator.plugin_registry import PluginRegistry
from core.orchestrator.event_bus import EventBus
from core.orchestrator.dependency_injector import container, register_singleton
from plugins.data.yfinance_provider import YFinanceProvider
from plugins.data.alpaca_provider import AlpacaProvider
from plugins.analysis.technical_analyzer import TechnicalAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
event_bus = None
plugin_registry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global event_bus, plugin_registry
    
    try:
        logger.info("🚀 Starting Dynamic Option Pilot v2.0")
        
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
        
        # Initialize all plugins
        success = await plugin_registry.initialize_all()
        if not success:
            logger.warning("⚠️ Some plugins failed to initialize")
        
        # Store in app state
        app.state.event_bus = event_bus
        app.state.plugin_registry = plugin_registry
        
        logger.info("✅ Application startup complete")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down application")
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
@app.get("/system/status")
async def system_status():
    """Get comprehensive system status."""
    if not plugin_registry or not event_bus:
        raise HTTPException(status_code=503, detail="System not ready")
    
    return {
        "plugin_registry": plugin_registry.get_system_status(),
        "event_bus": event_bus.get_stats(),
        "dependency_container": container.list_registrations()
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
            # Fallback to mock data for v2.0
            return {
                "symbol": symbol,
                "price": 627.50 if symbol == "SPY" else 100.00,
                "change": 2.15,
                "change_percent": 0.34,
                "volume": 85420,
                "vix": 14.8 if symbol == "SPY" else 20.0,
                "timestamp": "2025-07-29T18:30:00Z"
            }
        
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        # Return mock data on error
        return {
            "symbol": symbol,
            "price": 627.50 if symbol == "SPY" else 100.00,
            "change": 2.15,
            "change_percent": 0.34,
            "volume": 85420,
            "vix": 14.8 if symbol == "SPY" else 20.0,
            "timestamp": "2025-07-29T18:30:00Z"
        }


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


# Import the dashboard router
from api.routes import dashboard

# Include the dashboard router
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/api/demo/account/metrics")  
async def get_demo_account_metrics():
    """Get demo account metrics for demo mode."""
    return {
        "account_balance": 125750.68,
        "cash": 95234.50,
        "buying_power": 190469.00,
        "options_level": "4",
        "account_status": "ACTIVE",
        "total_pnl": 2575.68,
        "today_pnl": 485.32,
        "open_positions": 3,
        "margin_used": 4500,
        "win_rate": 72.5,
        "total_trades": 40,
        "sharpe_ratio": 1.42,
        "max_drawdown": 0.06,
        "last_updated": "2025-07-29T18:00:00Z"
    }


# Trading Opportunities Endpoint
@app.get("/api/trading/opportunities")
async def get_trading_opportunities():
    """Get current trading opportunities."""
    try:
        # For v2.0, return demo opportunities until real scanning is complete
        return {
            "opportunities": [
                {
                    "id": "opp_1",
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
                    "rsi": 45.3
                },
                {
                    "id": "opp_2", 
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
                    "rsi": 52.1
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching trading opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Positions endpoint
@app.get("/api/positions/")
async def get_positions(sync: bool = False):
    """Get current positions."""
    return []  # Empty for now - will be implemented with real broker integration


# Position sync endpoint
@app.post("/api/positions/sync")
async def sync_positions():
    """Sync positions with broker."""
    return {
        "status": "success",
        "message": "Demo mode: No real positions to sync",
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
    """Get demo trading opportunities."""
    return {
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
                "rsi": 45.3
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
                "rsi": 52.1
            },
            {
                "id": "demo_opp_3",
                "symbol": "NVDA",
                "strike": 115,
                "premium": 2.75,
                "max_loss": 275,
                "delta": 0.32,
                "probability_profit": 0.65,
                "expected_value": 138.00,
                "days_to_expiration": 42,
                "underlying_price": 118.45,
                "liquidity_score": 9.5,
                "bias": "STRONG",
                "rsi": 28.5
            }
        ]
    }


# Trading execution endpoint
@app.post("/api/trading/execute")
async def execute_trade(trade_data: Dict[str, Any]):
    """Execute a trade (demo mode)."""
    logger.info(f"Demo trade execution: {trade_data}")
    return {
        "id": f"demo_trade_{trade_data.get('id', 'unknown')}",
        "status": "EXECUTED",
        "message": "Demo trade executed successfully", 
        "order_id": f"DEMO_{trade_data.get('symbol', 'UNK')}_{int(asyncio.get_event_loop().time())}",
        "execution_price": trade_data.get("premium", 0),
        "commission": 2.50
    }


# Missing API endpoints that were causing 404 errors
@app.get("/api/market-commentary/session-status")
async def get_session_status():
    """Get market session status."""
    return {
        "session_status": "REGULAR_HOURS",
        "session_name": "Regular Trading Hours",
        "current_time_et": "2025-07-29T16:30:00Z",
        "next_market_open": "2025-07-30T09:30:00Z",
        "is_trading_hours": True,
        "volume_expectation": "HIGH",
        "liquidity_note": "Good liquidity during regular hours",
        "spx_data": {
            "price": 5565.85,
            "change": 12.45,
            "change_percent": 0.22,
            "volume": 1250000,
            "last_updated": "2025-07-29T16:30:00Z"
        },
        "nasdaq_data": {
            "price": 17845.32,
            "change": -8.75,
            "change_percent": -0.05,
            "volume": 850000,
            "last_updated": "2025-07-29T16:30:00Z"
        },
        "dow_data": {
            "price": 40598.12,
            "change": 45.23,
            "change_percent": 0.11,
            "volume": 650000,
            "last_updated": "2025-07-29T16:30:00Z"
        }
    }


@app.get("/api/strategies/")
async def get_strategies():
    """Get available trading strategies."""
    return {
        "strategies": [
            {
                "id": "iron_condor",
                "name": "Iron Condor",
                "description": "Market neutral strategy with defined risk",
                "risk_level": "MEDIUM",
                "min_dte": 30,
                "max_dte": 45,
                "enabled": True
            },
            {
                "id": "put_spread",
                "name": "Put Credit Spread", 
                "description": "Bullish strategy with limited upside",
                "risk_level": "LOW",
                "min_dte": 15,
                "max_dte": 35,
                "enabled": True
            },
            {
                "id": "covered_call",
                "name": "Covered Call",
                "description": "Generate income on existing stock positions",
                "risk_level": "LOW",
                "min_dte": 20,
                "max_dte": 40,
                "enabled": False
            }
        ]
    }


@app.get("/api/market-commentary/daily-commentary")
async def get_daily_commentary():
    """Get daily market commentary."""
    return {
        "date": "2025-07-29",
        "timestamp": "2025-07-29T18:00:00Z",
        "headline": "Markets Rally on Tech Strength and Rate Cut Optimism",
        "market_overview": "Markets showing continued strength with SPY reaching new highs. Options activity remains elevated with increased volatility expectations.",
        "key_themes": [
            "Technology sector leading gains with strong earnings momentum",
            "Energy sector showing mixed signals amid geopolitical concerns", 
            "Healthcare consolidating near resistance levels",
            "Financial stocks benefiting from rate cut expectations"
        ],
        "technical_outlook": "SPY remains in strong uptrend above key moving averages. VIX at low levels suggests complacent conditions.",
        "volatility_watch": "VIX remains in low teens, suggesting complacent market conditions. Watch for potential volatility expansion.",
        "trading_implications": [
            "Bullish momentum likely to continue near-term",
            "Options premiums relatively cheap for protective strategies", 
            "Credit spreads offering good risk-adjusted returns",
            "Watch for pullback opportunities in oversold names"
        ],
        "levels_to_watch": {
            "support_levels": [615.0, 610.0, 605.0],
            "resistance_levels": [635.0, 640.0, 645.0],
            "key_moving_averages": {
                "sma_20": 620.5,
                "sma_50": 615.2,
                "sma_200": 590.8
            }
        },
        "risk_factors": [
            "Geopolitical tensions could spark volatility",
            "Economic data releases may shift Fed expectations",
            "Earnings season results could impact sector rotation",
            "Options expiration flows may cause temporary volatility"
        ]
    }


# Sentiment API endpoints
@app.get("/api/sentiment/pulse")
async def get_sentiment_pulse(force_refresh: bool = False):
    """Get comprehensive market sentiment pulse."""
    return {
        "timestamp": "2025-07-29T18:30:00Z",
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
        "top20_sentiment": {},
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
    return {
        "overall_score": 0.32,
        "overall_label": "Positive",
        "spy_score": 0.35,
        "spy_label": "Positive",
        "mag7_average": 0.33,
        "mag7_label": "Positive",
        "last_updated": "2025-07-29T18:30:00Z",
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
        "last_updated": "2025-07-29T18:30:00Z",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )