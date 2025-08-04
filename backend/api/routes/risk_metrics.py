from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime
import logging

# We'll create the alpaca provider in the dependency function
from services.greeks_calculator import get_greeks_calculator

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_alpaca_service():
    """Dependency to get Alpaca provider"""
    # This should ideally come from dependency injection
    # For now, create a new instance (not ideal but functional)
    from plugins.data.alpaca_provider import AlpacaProvider
    from core.orchestrator.base_plugin import PluginConfig
    import os
    
    config = PluginConfig(
        settings={
            'api_key': os.getenv('ALPACA_API_KEY'),
            'secret_key': os.getenv('ALPACA_SECRET_KEY'),
            'paper_trading': os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        }
    )
    
    provider = AlpacaProvider(config)
    await provider.initialize()
    return provider

@router.get("/portfolio")
async def get_portfolio_risk_metrics(alpaca_service = Depends(get_alpaca_service)) -> Dict[str, Any]:
    """Get portfolio-level risk metrics including aggregated Greeks"""
    try:
        # Get all positions
        positions = await alpaca_service.get_positions()
        
        # Filter options positions
        options_positions = [p for p in positions if p.get('type') in ['CALL', 'PUT']]
        stock_positions = [p for p in positions if p.get('type') == 'STOCK']
        
        # Calculate portfolio Greeks
        calculator = get_greeks_calculator()
        portfolio_greeks = calculator.calculate_portfolio_greeks(options_positions)
        
        # Calculate position metrics
        total_positions = len(positions)
        options_count = len(options_positions)
        stocks_count = len(stock_positions)
        
        # Calculate portfolio value metrics
        total_market_value = sum(p.get('market_value', 0) for p in positions)
        total_pnl = sum(p.get('pnl', 0) for p in positions)
        
        # Calculate risk concentration
        concentration_risk = 0.0
        if total_positions > 0:
            # Simple concentration risk: what % of portfolio is in largest position
            largest_position = max((abs(p.get('market_value', 0)) for p in positions), default=0)
            concentration_risk = (largest_position / max(total_market_value, 1)) * 100
        
        # Calculate time decay risk (total theta)
        daily_theta_risk = portfolio_greeks.get('total_theta', 0.0)
        
        # Calculate directional risk (net delta)
        directional_risk = portfolio_greeks.get('total_delta', 0.0)
        
        # Risk score calculation (0-100, higher = more risky)
        risk_factors = []
        
        # Concentration risk factor (0-30 points)
        risk_factors.append(min(concentration_risk * 0.3, 30))
        
        # Time decay risk factor (0-25 points)  
        theta_risk_factor = min(abs(daily_theta_risk) / 10.0 * 25, 25)
        risk_factors.append(theta_risk_factor)
        
        # Directional risk factor (0-25 points)
        directional_risk_factor = min(abs(directional_risk) / 50.0 * 25, 25)
        risk_factors.append(directional_risk_factor)
        
        # Diversification factor (0-20 points, fewer positions = higher risk)
        diversification_risk = max(20 - total_positions * 2, 0)
        risk_factors.append(diversification_risk)
        
        overall_risk_score = sum(risk_factors)
        
        # Risk level categorization 
        if overall_risk_score < 25:
            risk_level = "LOW"
            risk_color = "green"
        elif overall_risk_score < 50:
            risk_level = "MODERATE"
            risk_color = "yellow"
        elif overall_risk_score < 75:
            risk_level = "HIGH"
            risk_color = "orange"
        else:
            risk_level = "EXTREME"
            risk_color = "red"
        
        return {
            "portfolio_summary": {
                "total_positions": total_positions,
                "options_positions": options_count,
                "stock_positions": stocks_count,
                "total_market_value": round(total_market_value, 2),
                "total_pnl": round(total_pnl, 2),
                "pnl_percentage": round((total_pnl / max(abs(total_market_value - total_pnl), 1)) * 100, 2)
            },
            "portfolio_greeks": {
                "total_delta": portfolio_greeks.get('total_delta', 0.0),
                "total_gamma": portfolio_greeks.get('total_gamma', 0.0), 
                "total_theta": portfolio_greeks.get('total_theta', 0.0),
                "total_vega": portfolio_greeks.get('total_vega', 0.0),
                "total_rho": portfolio_greeks.get('total_rho', 0.0)
            },
            "risk_metrics": {
                "overall_risk_score": round(overall_risk_score, 1),
                "risk_level": risk_level,
                "risk_color": risk_color,
                "concentration_risk": round(concentration_risk, 1),
                "daily_theta_risk": round(daily_theta_risk, 2),
                "directional_risk": round(directional_risk, 2),
                "diversification_score": max(0, 10 - diversification_risk/2)
            },
            "risk_breakdown": {
                "concentration": {
                    "score": round(risk_factors[0], 1),
                    "description": f"Largest position is {concentration_risk:.1f}% of portfolio"
                },
                "time_decay": {
                    "score": round(risk_factors[1], 1), 
                    "description": f"Portfolio losing ${abs(daily_theta_risk):.2f}/day to time decay"
                },
                "directional": {
                    "score": round(risk_factors[2], 1),
                    "description": f"Net delta exposure: {directional_risk:.2f}"
                },
                "diversification": {
                    "score": round(risk_factors[3], 1),
                    "description": f"Portfolio has {total_positions} positions"
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio risk metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating risk metrics: {str(e)}")

@router.get("/greeks")
async def get_detailed_greeks(alpaca_service = Depends(get_alpaca_service)) -> Dict[str, Any]:
    """Get detailed Greeks breakdown by position"""
    try:
        # Get all positions
        positions = await alpaca_service.get_positions()
        
        # Filter and organize options positions
        options_positions = [p for p in positions if p.get('type') in ['CALL', 'PUT']]
        
        # Group by underlying
        by_underlying = {}
        for pos in options_positions:
            underlying = pos.get('underlying', 'UNKNOWN')
            if underlying not in by_underlying:
                by_underlying[underlying] = {
                    'positions': [],
                    'total_delta': 0.0,
                    'total_gamma': 0.0,
                    'total_theta': 0.0,
                    'total_vega': 0.0
                }
            
            # Add position to underlying group
            by_underlying[underlying]['positions'].append({
                'symbol': pos.get('symbol'),
                'type': pos.get('type'),
                'strike': pos.get('strike'),
                'quantity': pos.get('quantity'),
                'expiration': pos.get('expiration'),
                'delta': pos.get('delta', 0.0),
                'gamma': pos.get('gamma', 0.0),
                'theta': pos.get('theta', 0.0),
                'vega': pos.get('vega', 0.0)
            })
            
            # Add to underlying totals (weighted by quantity)
            qty = pos.get('quantity', 0)
            by_underlying[underlying]['total_delta'] += pos.get('delta', 0.0) * qty
            by_underlying[underlying]['total_gamma'] += pos.get('gamma', 0.0) * qty  
            by_underlying[underlying]['total_theta'] += pos.get('theta', 0.0) * qty
            by_underlying[underlying]['total_vega'] += pos.get('vega', 0.0) * qty
        
        # Round the totals
        for underlying_data in by_underlying.values():
            for key in ['total_delta', 'total_gamma', 'total_theta', 'total_vega']:
                underlying_data[key] = round(underlying_data[key], 4)
        
        return {
            "by_underlying": by_underlying,
            "summary": {
                "total_options_positions": len(options_positions),
                "underlyings_count": len(by_underlying),
                "underlyings": list(by_underlying.keys())
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed Greeks: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting Greeks details: {str(e)}")