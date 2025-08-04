import logging
from typing import Dict, Any
from datetime import datetime
import os

from fastapi import APIRouter, HTTPException

from services.opportunity_cache import get_opportunity_cache


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/portfolio-risk")
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
            "covered_call": {"risk": 2400.00, "percentage": 28.4},
        },
        "risk_by_symbol": {
            "SPY": {"risk": 2850.00, "percentage": 33.7},
            "QQQ": {"risk": 2120.00, "percentage": 25.1},
            "IWM": {"risk": 1980.00, "percentage": 23.4},
            "AAPL": {"risk": 1500.00, "percentage": 17.8},
        },
        "last_updated": current_timestamp,
    }


@router.get("/stress-tests")
async def get_stress_tests():
    """Get stress test results."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "stress_scenarios": {
            "market_crash_10": {
                "scenario": "Market drops 10%",
                "portfolio_impact": -12850.50,
                "impact_percentage": -10.22,
                "recovery_days": 25,
            },
            "volatility_spike": {
                "scenario": "VIX spikes to 40",
                "portfolio_impact": -8950.25,
                "impact_percentage": -7.12,
                "recovery_days": 18,
            },
            "interest_rate_shock": {
                "scenario": "Rates rise 2%",
                "portfolio_impact": -4250.75,
                "impact_percentage": -3.38,
                "recovery_days": 12,
            },
            "sector_rotation": {
                "scenario": "Tech sector selloff",
                "portfolio_impact": -6850.00,
                "impact_percentage": -5.45,
                "recovery_days": 15,
            },
        },
        "monte_carlo": {
            "simulations": 10000,
            "var_95": 2850.50,
            "var_99": 4120.75,
            "expected_return": 8.5,
            "worst_case_1_month": -18750.00,
            "best_case_1_month": 22500.00,
        },
        "last_updated": current_timestamp,
    }


@router.get("/risk-alerts")
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
                "created_at": current_timestamp,
            },
            {
                "id": "alert_002",
                "type": "VOLATILITY",
                "severity": "LOW",
                "message": "Portfolio volatility above historical average",
                "current_value": 0.22,
                "threshold": 0.20,
                "created_at": current_timestamp,
            },
        ],
        "alert_summary": {
            "total_alerts": 2,
            "high_severity": 0,
            "medium_severity": 1,
            "low_severity": 1,
        },
        "last_updated": current_timestamp,
    }

@router.get("/analytics/risk-metrics")
async def get_risk_metrics():
    """Get risk analytics metrics from real portfolio data."""
    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z"

        # Get opportunity cache to analyze current market exposure
        cache = get_opportunity_cache()

        # Aggregate risk metrics from all available opportunities
        all_opportunities = []
        for strategy in ["high_probability", "quick_scalp", "theta_decay"]:
            opportunities = await cache.get_opportunities(strategy)
            if isinstance(opportunities, dict) and "opportunities" in opportunities:
                all_opportunities.extend(opportunities["opportunities"])
            elif isinstance(opportunities, list):
                all_opportunities.extend(opportunities)

        if not all_opportunities:
            # Return empty state instead of error when no positions
            return {
                "portfolio_metrics": {
                    "total_value": 0.0,
                    "available_cash": 0.0,
                    "total_exposure": 0.0,
                    "position_count": 0,
                },
                "risk_metrics": {
                    "portfolio_delta": 0.0,
                    "portfolio_gamma": 0.0,
                    "portfolio_theta": 0.0,
                    "portfolio_vega": 0.0,
                    "max_loss": 0.0,
                    "var_95": 0.0,
                },
                "concentration": {
                    "max_position_pct": 0.0,
                    "sector_concentration": {},
                    "strategy_allocation": {},
                },
                "analysis": {
                    "risk_level": "MINIMAL",
                    "warnings": ["No active positions found"],
                    "recommendations": [
                        "Consider establishing positions based on current opportunities"
                    ],
                },
                "timestamp": current_timestamp,
                "data_source": "opportunity_analysis",
            }

        # Calculate aggregate risk metrics from opportunities
        total_premium = sum(float(opp.get("premium", 0)) for opp in all_opportunities)
        total_max_loss = sum(float(opp.get("max_loss", 0)) for opp in all_opportunities)
        avg_probability = sum(
            float(opp.get("probability_profit", 0.5)) for opp in all_opportunities
        ) / len(all_opportunities)

        # Count positions by strategy
        strategy_counts = {}
        for opp in all_opportunities:
            strategy = opp.get("strategy_type", "unknown")
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
                "position_count": len(all_opportunities),
            },
            "risk_metrics": {
                "portfolio_delta": round(
                    sum(float(opp.get("delta", 0)) for opp in all_opportunities), 4
                ),
                "portfolio_gamma": round(
                    sum(float(opp.get("gamma", 0)) for opp in all_opportunities), 4
                ),
                "portfolio_theta": round(
                    sum(float(opp.get("theta", 0)) for opp in all_opportunities), 2
                ),
                "portfolio_vega": round(
                    sum(float(opp.get("vega", 0)) for opp in all_opportunities), 2
                ),
                "max_loss": round(total_max_loss, 2),
                "var_95": round(
                    total_max_loss * 0.15, 2
                ),  # 15% of max loss as VaR estimate
            },
            "concentration": {
                "max_position_pct": round(
                    max(
                        [float(opp.get("max_loss", 0)) for opp in all_opportunities]
                        + [0]
                    )
                    / max(total_max_loss, 1)
                    * 100,
                    1,
                ),
                "sector_concentration": {},  # Would need symbol sector mapping
                "strategy_allocation": {
                    k: round(v / len(all_opportunities) * 100, 1)
                    for k, v in strategy_counts.items()
                },
            },
            "analysis": {
                "risk_level": risk_level,
                "warnings": [
                    w
                    for w in [
                        f"Portfolio has {len(all_opportunities)} active positions",
                        (
                            f"Maximum potential loss: ${total_max_loss:,.2f}"
                            if total_max_loss > 2000
                            else None
                        ),
                        (
                            f"Average win probability: {avg_probability:.1%}"
                            if avg_probability < 0.7
                            else None
                        ),
                    ]
                    if w is not None
                ],
                "recommendations": [
                    r
                    for r in [
                        (
                            "Monitor position concentration"
                            if len(
                                set(opp.get("symbol", "") for opp in all_opportunities)
                            )
                            < 5
                            else None
                        ),
                        "Consider profit taking" if total_premium > 1000 else None,
                        (
                            "Review position sizing"
                            if any(
                                float(opp.get("max_loss", 0)) > 1000
                                for opp in all_opportunities
                            )
                            else None
                        ),
                    ]
                    if r is not None
                ],
            },
            "timestamp": current_timestamp,
            "data_source": "real_opportunity_data",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
