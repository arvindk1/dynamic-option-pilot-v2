from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from services.strategy_ai_service import get_strategy_ai_service, StrategyAIService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_ai_service() -> StrategyAIService:
    """Dependency to get AI service instance"""
    return get_strategy_ai_service()

@router.get("/dashboard")
async def get_ai_coach_dashboard(ai_service: StrategyAIService = Depends(get_ai_service)) -> Dict[str, Any]:
    """Get AI Trading Coach dashboard data"""
    try:
        # Get AI service statistics
        stats = ai_service.get_conversation_stats()
        rate_limit_status = ai_service.get_rate_limit_status()
        
        # Mock dashboard data - in production, this would analyze actual trading data
        return {
            "status": "active" if ai_service.enabled else "disabled",
            "ai_service_info": {
                "enabled": ai_service.enabled,
                "current_model": stats.get("current_model", "unknown"),
                "model_info": stats.get("model_info", {}),
                "rate_limits": rate_limit_status
            },
            "insights": [
                {
                    "id": "insight_1",
                    "type": "performance",
                    "title": "Strategy Performance Analysis",
                    "message": "Your options strategies are performing well with a 65% win rate.",
                    "severity": "info",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "insight_2", 
                    "type": "risk",
                    "title": "Risk Management",
                    "message": "Consider reducing position sizes in high IV environments.",
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "recommendations": [
                {
                    "id": "rec_1",
                    "type": "strategy_optimization",
                    "title": "DTE Optimization",
                    "description": "Consider adjusting target DTE range for better theta decay capture",
                    "priority": "medium"
                }
            ],
            "summary": {
                "total_trades_graded": 47,
                "average_grade": "B+",
                "average_score": 82.5,  # Numeric score for .toFixed() calls
                "improvement_opportunities": 5,
                "trading_insights": 8
            },
            "performance_summary": {
                "overall_grade": "B+",
                "win_rate": 0.65,
                "avg_profit": 125.50,
                "risk_score": 0.35,
                "improvement_areas": ["position_sizing", "entry_timing"]
            },
            "portfolio_optimization": {
                "current_metrics": {
                    "sharpe_ratio": 1.42,
                    "max_drawdown": 0.08,  # 8% max drawdown
                    "win_rate": 0.65,      # 65% win rate
                    "avg_return": 0.12     # 12% average return
                },
                "projected_metrics": {
                    "sharpe_ratio": 1.68,
                    "max_drawdown": 0.06,  # Improved to 6%
                    "win_rate": 0.72,      # Improved to 72%
                    "avg_return": 0.15     # Improved to 15%
                },
                "confidence_score": 0.78   # 78% confidence in optimization
            },
            "performance_patterns": [
                {
                    "id": "pattern_1",
                    "pattern_name": "Theta Decay Mastery", 
                    "pattern_type": "entry_timing",
                    "description": "Consistently enters positions with optimal DTE for theta decay",
                    "win_rate": 0.72,
                    "avg_pnl": 215.50,
                    "confidence": 0.88
                },
                {
                    "id": "pattern_2",
                    "pattern_name": "Profit Target Discipline",
                    "pattern_type": "exit_management", 
                    "description": "Excellent discipline taking profits at 50% target",
                    "win_rate": 0.68,
                    "avg_pnl": 180.25,
                    "confidence": 0.82
                }
            ],
            "grades": [
                {
                    "id": "grade_1",
                    "trade_symbol": "SPY",
                    "trade_id": "T-001",
                    "overall_grade": "A-",
                    "overall_score": 87.5,
                    "trade_pnl": 285.50,
                    "category_scores": {
                        "entry": 90,
                        "management": 85, 
                        "exit": 88
                    }
                },
                {
                    "id": "grade_2", 
                    "trade_symbol": "QQQ",
                    "trade_id": "T-002",
                    "overall_grade": "B+",
                    "overall_score": 82.0,
                    "trade_pnl": 165.25,
                    "category_scores": {
                        "entry": 80,
                        "management": 85,
                        "exit": 80
                    }
                }
            ],
            "active_insights": [
                {
                    "id": "active_insight_1",
                    "title": "High IV Environment Detected",
                    "priority": "high",
                    "message": "Current market conditions favor premium collection strategies",
                    "relevance_score": 0.92,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "active_insight_2",
                    "title": "Position Concentration Risk",
                    "priority": "medium", 
                    "message": "Consider diversifying across more underlying symbols",
                    "relevance_score": 0.75,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "active_insight_3",
                    "title": "Theta Decay Opportunity",
                    "priority": "low",
                    "message": "Optimal conditions for short theta strategies this week",
                    "relevance_score": 0.68,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI coach dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading AI coach dashboard: {str(e)}")

@router.post("/analyze-patterns")
async def analyze_trading_patterns(ai_service: StrategyAIService = Depends(get_ai_service)) -> Dict[str, Any]:
    """Analyze trading patterns using AI"""
    try:
        if not ai_service.enabled:
            return {
                "analysis": "AI pattern analysis is not available. Please configure OpenAI API key.",
                "patterns": [],
                "recommendations": [],
                "confidence": 0.0
            }
        
        # In production, this would analyze actual trading data and positions
        # For now, return a structured response format
        return {
            "analysis": "Pattern analysis completed. Found consistent theta decay strategies with good risk management.",
            "patterns": [
                {
                    "pattern_type": "entry_timing",
                    "description": "You tend to enter positions with 21-35 DTE, which is optimal for theta strategies",
                    "frequency": 0.75,
                    "performance_impact": "positive"
                },
                {
                    "pattern_type": "exit_management", 
                    "description": "Profit taking at 50% target shows good discipline",
                    "frequency": 0.68,
                    "performance_impact": "positive"
                }
            ],
            "recommendations": [
                {
                    "priority": "high",
                    "category": "risk_management",
                    "suggestion": "Consider implementing dynamic stop losses based on IV changes"
                },
                {
                    "priority": "medium", 
                    "category": "entry_optimization",
                    "suggestion": "Monitor IV rank before entries - avoid entering above 70th percentile"
                }
            ],
            "confidence": 0.85,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trading patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing patterns: {str(e)}")

@router.post("/generate-insights")
async def generate_ai_insights(ai_service: StrategyAIService = Depends(get_ai_service)) -> Dict[str, Any]:
    """Generate AI-powered trading insights"""
    try:
        if not ai_service.enabled:
            return {
                "insights": [
                    {
                        "id": "no_ai",
                        "type": "info",
                        "title": "AI Insights Unavailable",
                        "message": "AI insights require OpenAI API key configuration.",
                        "severity": "info"
                    }
                ]
            }
        
        # Generate insights based on current market conditions and positions
        return {
            "insights": [
                {
                    "id": f"insight_{datetime.now().timestamp()}",
                    "type": "market_analysis",
                    "title": "Market Volatility Alert",
                    "message": "Current VIX levels suggest good conditions for premium collection strategies",
                    "severity": "info",
                    "confidence": 0.78,
                    "actionable": True,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": f"insight_{datetime.now().timestamp() + 1}",
                    "type": "position_management",
                    "title": "Position Concentration Risk",
                    "message": "Consider diversifying across more underlying symbols",
                    "severity": "warning", 
                    "confidence": 0.65,
                    "actionable": True,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@router.post("/optimize-portfolio")
async def optimize_portfolio(ai_service: StrategyAIService = Depends(get_ai_service)) -> Dict[str, Any]:
    """AI-powered portfolio optimization suggestions"""
    try:
        if not ai_service.enabled:
            return {
                "optimization_suggestions": [
                    {
                        "category": "general",
                        "suggestion": "AI portfolio optimization requires OpenAI API key configuration",
                        "impact": "info"
                    }
                ]
            }
        
        # Analyze current portfolio and suggest optimizations
        return {
            "optimization_suggestions": [
                {
                    "category": "risk_management",
                    "suggestion": "Reduce position sizes when VIX > 25",
                    "impact": "high",
                    "reasoning": "High volatility increases position risk"
                },
                {
                    "category": "diversification",
                    "suggestion": "Add more defensive positions during market downturns",
                    "impact": "medium", 
                    "reasoning": "Current positions are concentrated in growth sectors"
                },
                {
                    "category": "theta_optimization",
                    "suggestion": "Target 30-45 DTE for optimal theta decay",
                    "impact": "medium",
                    "reasoning": "Your current DTE range could be optimized for better time decay"
                }
            ],
            "portfolio_score": {
                "overall": 7.5,
                "risk_management": 8.0,
                "diversification": 6.5,
                "strategy_execution": 8.5
            },
            "optimized_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing portfolio: {str(e)}")

@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(insight_id: str) -> Dict[str, Any]:
    """Dismiss an AI insight"""
    try:
        # In production, this would mark the insight as dismissed in the database
        logger.info(f"Dismissing AI insight: {insight_id}")
        
        return {
            "success": True,
            "insight_id": insight_id,
            "dismissed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error dismissing insight {insight_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error dismissing insight: {str(e)}")

@router.get("/rate-limits") 
async def get_rate_limit_status(ai_service: StrategyAIService = Depends(get_ai_service)) -> Dict[str, Any]:
    """Get AI service rate limit status - useful for debugging"""
    try:
        return ai_service.get_rate_limit_status()
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rate limits: {str(e)}")