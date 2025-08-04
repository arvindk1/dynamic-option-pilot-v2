from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging
import os

from plugins.data.alpaca_provider import AlpacaProvider
from core.orchestrator.base_plugin import PluginConfig

logger = logging.getLogger(__name__)
router = APIRouter()

# Global Alpaca provider instance
_alpaca_provider = None

async def get_alpaca_provider() -> AlpacaProvider:
    """Get or create Alpaca provider instance."""
    global _alpaca_provider
    
    if _alpaca_provider is None:
        config = PluginConfig(
            settings={
                'api_key': os.getenv('ALPACA_API_KEY'),
                'secret_key': os.getenv('ALPACA_SECRET_KEY'),
                'paper_trading': os.getenv('PAPER_TRADING', 'true').lower() == 'true'
            }
        )
        
        _alpaca_provider = AlpacaProvider(config)
        await _alpaca_provider.initialize()
    
    return _alpaca_provider

async def check_broker_connection() -> bool:
    """Check if broker (Alpaca) is connected and available."""
    try:
        provider = await get_alpaca_provider()
        # Test connection by getting account info
        account_info = await provider.get_account_info()
        return bool(account_info.get('account_id'))
    except Exception as e:
        logger.warning(f"Broker connection check failed: {e}")
        return False

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get dashboard metrics - uses real Alpaca data when available"""
    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check if real broker API is available
        broker_connected = await check_broker_connection()
        
        if broker_connected:
            # Return real Alpaca broker data
            try:
                provider = await get_alpaca_provider()
                account_info = await provider.get_account_info()
                positions = await provider.get_positions()
                
                # Calculate basic trading metrics from positions
                open_positions = len([p for p in positions if p.get('status') == 'OPEN'])
                total_pnl = sum(p.get('pnl', 0) for p in positions)
                
                return {
                    "data_state": "live",
                    "broker": "Alpaca Paper Trading" if os.getenv('PAPER_TRADING', 'true').lower() == 'true' else "Alpaca Live",
                    
                    # Real account data from Alpaca
                    "account_balance": account_info.get('account_balance', 0.0),
                    "cash": account_info.get('cash', 0.0),
                    "buying_power": account_info.get('buying_power', 0.0),
                    "account_status": account_info.get('account_status', 'UNKNOWN'),
                    "account_id": account_info.get('account_id', 'N/A'),
                    
                    # Trading statistics from positions
                    "total_pnl": total_pnl,
                    "pnl_percentage": (total_pnl / account_info.get('account_balance', 1)) * 100 if account_info.get('account_balance', 0) > 0 else 0.0,
                    "today_pnl": 0.0,  # Would need daily tracking
                    "positions_open": open_positions,
                    
                    # Default/calculated values
                    "win_rate": 0.0,  # Would need trade history analysis
                    "total_trades": len(positions),
                    "winning_trades": 0,  # Would need trade analysis
                    "sharpe_ratio": 0.0,  # Would need historical performance data
                    "max_drawdown": 0.0,  # Would need historical performance data
                    
                    # Market data indicators (defaults for now)
                    "vix": 18.5,  # Would get from market data provider
                    "iv_rank": 0.45,  # Would calculate from options data
                    
                    "last_updated": current_timestamp,
                    "is_demo": False
                }
            except Exception as e:
                logger.error(f"Error getting real broker data, falling back to demo: {e}")
                broker_connected = False  # Fall through to demo data
        
        if not broker_connected:
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
                "is_demo": True
            }
            
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard metrics: {str(e)}")

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
                date = now - timedelta(days=days-i-1)
                # Generate realistic but consistent daily changes
                daily_change = random.uniform(-800, 1200) * (0.7 + 0.3 * random.random())
                cumulative_pnl += daily_change
                
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "daily_pnl": round(daily_change, 2),
                    "cumulative_pnl": round(cumulative_pnl, 2),
                    "account_value": round(base_value + cumulative_pnl, 2)
                })
            
            return {
                "data_state": "demo",
                "warning": "🚨 DEMO MODE - Connect broker for live performance data",
                "demo_notice": "This is simulated performance data for development purposes",
                "start_date": (now - timedelta(days=days)).isoformat(),
                "end_date": now.isoformat(),
                "data": data,
                "is_demo": True,
                "last_updated": current_timestamp
            }
            
    except Exception as e:
        logger.error(f"Error getting performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))