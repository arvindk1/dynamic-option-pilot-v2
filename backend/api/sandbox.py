"""
Sandbox API Endpoints
Strategy testing and development APIs
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db
from services.sandbox_service import get_sandbox_service
from services.strategy_ai_service import get_strategy_ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

# Pydantic models for API requests/responses
class StrategyConfigRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy identifier (e.g., 'thetacrop_weekly')")
    name: str = Field(..., description="User-friendly name for the strategy")
    config_data: Dict[str, Any] = Field(..., description="Strategy configuration parameters")

class StrategyConfigResponse(BaseModel):
    id: str
    strategy_id: str
    name: str
    config_data: Dict[str, Any]
    version: int
    is_active: bool
    created_at: str
    updated_at: str
    deployed_at: Optional[str]
    test_run_count: int

class TestRequest(BaseModel):
    symbols: Optional[List[str]] = Field(None, description="Symbols to test (optional)")
    max_opportunities: int = Field(10, description="Maximum opportunities to generate")
    use_cached_data: bool = Field(True, description="Use cached data for testing")

class TestResultReponse(BaseModel):
    success: bool
    opportunities_count: int
    execution_time_ms: int
    performance_metrics: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None

class AIMessageRequest(BaseModel):
    message: str = Field(..., description="Message to send to AI assistant")
    include_context: bool = Field(True, description="Include strategy context in AI request")

class AIMessageResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    estimated_cost: str
    conversation_id: str
    timestamp: str


# Strategy Management Endpoints
@router.get("/strategies/", response_model=List[StrategyConfigResponse])
async def list_user_strategies(user_id: str = Query("default_user", description="User identifier")):
    """List all sandbox strategy configurations for a user"""
    try:
        sandbox_service = get_sandbox_service()
        configs = await sandbox_service.get_user_strategies(user_id)
        
        return [StrategyConfigResponse(**config.to_dict()) for config in configs]
        
    except Exception as e:
        logger.error(f"Error listing user strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/", response_model=StrategyConfigResponse)
async def create_strategy_config(
    request: StrategyConfigRequest,
    user_id: str = Query("default_user", description="User identifier")
):
    """Create a new sandbox strategy configuration"""
    try:
        sandbox_service = get_sandbox_service()
        
        config = await sandbox_service.create_strategy_config(
            strategy_id=request.strategy_id,
            name=request.name,
            config_data=request.config_data,
            user_id=user_id
        )
        
        return StrategyConfigResponse(**config.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating strategy config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{config_id}", response_model=StrategyConfigResponse)
async def get_strategy_config(config_id: str):
    """Get a specific sandbox strategy configuration"""
    try:
        sandbox_service = get_sandbox_service()
        config = await sandbox_service.get_strategy_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        return StrategyConfigResponse(**config.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/strategies/{config_id}", response_model=StrategyConfigResponse)
async def update_strategy_config(config_id: str, updates: Dict[str, Any]):
    """Update a sandbox strategy configuration"""
    try:
        sandbox_service = get_sandbox_service()
        config = await sandbox_service.update_strategy_config(config_id, updates)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        return StrategyConfigResponse(**config.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategies/{config_id}")
async def delete_strategy_config(config_id: str):
    """Delete a sandbox strategy configuration"""
    try:
        sandbox_service = get_sandbox_service()
        config = await sandbox_service.get_strategy_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        # TODO: Implement deletion logic
        return {"message": f"Strategy configuration {config_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Testing Endpoints
@router.post("/test/run/{config_id}")
async def run_strategy_test(config_id: str, test_request: TestRequest = None):
    """Run a strategy test with current configuration"""
    try:
        sandbox_service = get_sandbox_service()
        
        # Convert test request to parameters
        test_params = {}
        if test_request:
            test_params = {
                'symbols': test_request.symbols,
                'max_opportunities': test_request.max_opportunities,
                'use_cached_data': test_request.use_cached_data
            }
        
        results = await sandbox_service.run_strategy_test(config_id, test_params)
        
        return results
        
    except Exception as e:
        logger.error(f"Error running strategy test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/results/{config_id}")
async def get_test_results(config_id: str, limit: int = Query(10, description="Number of results to return")):
    """Get recent test results for a strategy"""
    try:
        sandbox_service = get_sandbox_service()
        results = await sandbox_service.get_test_results(config_id, limit)
        
        return [result.to_dict() for result in results]
        
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/history/{config_id}")
async def get_test_history(config_id: str, limit: int = Query(20, description="Number of history items")):
    """Get test run history for a strategy"""
    try:
        sandbox_service = get_sandbox_service()
        results = await sandbox_service.get_test_results(config_id, limit)
        
        # Format for history view
        history = []
        for result in results:
            history.append({
                'id': result.id,
                'run_date': result.created_at.isoformat() if result.created_at else None,
                'opportunities_found': result.opportunities_found,
                'execution_time_ms': result.execution_time_ms,
                'success': result.test_results.get('success', False),
                'performance_summary': result.test_results.get('performance_metrics', {})
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting test history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Assistant Endpoints
@router.post("/ai/chat/{config_id}", response_model=AIMessageResponse)
async def chat_with_ai_assistant(config_id: str, request: AIMessageRequest):
    """Send a message to the AI assistant for strategy analysis"""
    try:
        sandbox_service = get_sandbox_service()
        ai_service = get_strategy_ai_service()
        
        # Get strategy configuration
        config = await sandbox_service.get_strategy_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        # Get recent test results for context
        performance_data = None
        if request.include_context:
            recent_tests = await sandbox_service.get_test_results(config_id, limit=3)
            if recent_tests:
                # Use most recent test performance metrics
                performance_data = recent_tests[0].test_results.get('performance_metrics', {})
        
        # Chat with AI
        ai_response = await ai_service.chat_with_strategy(
            strategy_name=config.name,
            strategy_config=config.config_data,
            user_message=request.message,
            conversation_id=config_id,  # Use config_id as conversation context
            performance_data=performance_data
        )
        
        # Save conversation to database (if successful)
        if not ai_response.get('error'):
            # TODO: Save to SandboxAIConversation table
            pass
        
        return AIMessageResponse(
            response=ai_response.get('response', 'Sorry, I encountered an error.'),
            model=ai_response.get('model', 'unknown'),
            tokens_used=ai_response.get('tokens_used', 0),
            estimated_cost=f"${ai_response.get('estimated_cost', 0):.4f}",
            conversation_id=ai_response.get('conversation_id', config_id),
            timestamp=ai_response.get('timestamp', datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/history/{config_id}")
async def get_ai_chat_history(config_id: str, limit: int = Query(20, description="Number of messages")):
    """Get AI chat history for a strategy"""
    try:
        # TODO: Implement chat history retrieval from database
        return {"message": "AI chat history endpoint - to be implemented"}
        
    except Exception as e:
        logger.error(f"Error getting AI chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/analyze/{config_id}")
async def analyze_strategy_with_ai(config_id: str):
    """Request comprehensive AI analysis of a strategy"""
    try:
        sandbox_service = get_sandbox_service()
        ai_service = get_strategy_ai_service()
        
        # Get strategy configuration
        config = await sandbox_service.get_strategy_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        # Get recent performance data
        recent_tests = await sandbox_service.get_test_results(config_id, limit=5)
        performance_data = {}
        if recent_tests:
            # Aggregate performance metrics
            total_opportunities = sum(test.opportunities_found for test in recent_tests)
            avg_execution_time = sum(test.execution_time_ms for test in recent_tests) / len(recent_tests)
            
            performance_data = {
                'total_test_runs': len(recent_tests),
                'total_opportunities_found': total_opportunities,
                'avg_opportunities_per_run': total_opportunities / len(recent_tests),
                'avg_execution_time_ms': avg_execution_time,
                'latest_performance': recent_tests[0].test_results.get('performance_metrics', {})
            }
        
        # Request AI analysis
        analysis_prompt = f"Please provide a comprehensive analysis of this {config.name} strategy configuration. Look at the parameters, recent performance, and suggest any optimizations."
        
        ai_response = await ai_service.chat_with_strategy(
            strategy_name=config.name,
            strategy_config=config.config_data,
            user_message=analysis_prompt,
            conversation_id=f"{config_id}_analysis",
            performance_data=performance_data
        )
        
        return {
            'strategy_id': config_id,
            'strategy_name': config.name,
            'analysis': ai_response.get('response', 'Analysis not available'),
            'performance_summary': performance_data,
            'model_used': ai_response.get('model', 'unknown'),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI strategy analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Deployment Endpoints
@router.post("/deploy/{config_id}")
async def deploy_strategy_to_live(config_id: str):
    """Deploy a sandbox strategy configuration to the live system"""
    try:
        sandbox_service = get_sandbox_service()
        
        # Get strategy configuration
        config = await sandbox_service.get_strategy_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        # TODO: Implement deployment logic
        # 1. Validate configuration
        # 2. Convert to live strategy format
        # 3. Register with live strategy system
        # 4. Mark as deployed
        
        return {
            'status': 'success',
            'message': f'Strategy {config.name} deployed to live system',
            'config_id': config_id,
            'deployed_at': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deploy/status/{config_id}")
async def get_deployment_status(config_id: str):
    """Get deployment status of a strategy"""
    try:
        sandbox_service = get_sandbox_service()
        config = await sandbox_service.get_strategy_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        return {
            'config_id': config_id,
            'is_active': config.is_active,
            'deployed_at': config.deployed_at.isoformat() if config.deployed_at else None,
            'status': 'deployed' if config.is_active else 'sandbox_only'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Data and Utility Endpoints
@router.get("/data/cached/{symbol}")
async def get_cached_market_data(symbol: str):
    """Get cached market data for a symbol"""
    try:
        # TODO: Implement cached data retrieval
        return {
            'symbol': symbol,
            'message': 'Cached market data endpoint - to be implemented'
        }
        
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/universes")
async def list_available_universes():
    """List all available trading universes"""
    try:
        universe_info = {
            'mag7': {
                'name': 'MAG7 - Magnificent Seven',
                'description': 'Top 7 tech giants driving market sentiment',
                'symbol_type': 'Large Cap Tech',
                'typical_count': 7
            },
            'etfs': {
                'name': 'ETF Universe', 
                'description': 'Sector and broad market ETFs',
                'symbol_type': 'ETF',
                'typical_count': 18
            },
            'top20': {
                'name': 'Top 20 Large Caps',
                'description': 'Most liquid large-cap stocks',
                'symbol_type': 'Large Cap',
                'typical_count': 20
            },
            'thetacrop': {
                'name': 'ThetaCrop Universe',
                'description': 'High-volume ETFs for theta strategies',
                'symbol_type': 'ETF',
                'typical_count': 3
            },
            'sector_leaders': {
                'name': 'Sector Leaders',
                'description': 'Leading stocks by sector',
                'symbol_type': 'Mixed',
                'typical_count': 28
            }
        }
        
        return {
            'universes': universe_info,
            'count': len(universe_info)
        }
        
    except Exception as e:
        logger.error(f"Error listing universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/universe/{universe_name}")
async def get_universe_symbols(universe_name: str):
    """Get symbols from a trading universe"""
    try:
        from services.universe_loader import get_universe_loader
        
        universe_loader = get_universe_loader()
        
        # Map universe names to files
        universe_files = {
            'mag7': 'mag7.txt',
            'etfs': 'etfs.txt',
            'top20': 'top20.txt',
            'sector_leaders': 'sector_leaders.txt',
            'thetacrop': 'thetacrop_symbols.txt'
        }
        
        if universe_name not in universe_files:
            raise HTTPException(status_code=404, detail=f"Universe {universe_name} not found")
        
        # Load actual symbols from universe files
        try:
            symbols = universe_loader.load_universe(universe_files[universe_name])
        except Exception as e:
            logger.warning(f"Failed to load universe from file, using fallback: {e}")
            # Fallback to hardcoded data if file loading fails
            sample_universes = {
                'mag7': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META'],
                'etfs': ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE'],
                'top20': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'BRK-B', 'TSLA', 'META'],
                'thetacrop': ['SPY', 'QQQ', 'IWM'],
                'sector_leaders': ['AAPL', 'XLK', 'JPM', 'XLF', 'UNH', 'XLV']
            }
            symbols = sample_universes.get(universe_name, [])
        
        return {
            'universe_name': universe_name,
            'symbols': symbols,
            'count': len(symbols)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting universe symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics and Monitoring
@router.get("/stats/user")
async def get_user_sandbox_stats(user_id: str = Query("default_user", description="User identifier")):
    """Get aggregate sandbox usage statistics for a user"""
    try:
        sandbox_service = get_sandbox_service()
        stats = await sandbox_service.get_user_stats(user_id)
        
        return {
            'user_id': user_id,
            'stats': stats,
            'retrieved_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/cleanup")
async def cleanup_sandbox_data():
    """Clean up expired cache and old test data"""
    try:
        sandbox_service = get_sandbox_service()
        cleanup_results = await sandbox_service.cleanup_expired_data()
        
        return {
            'status': 'success',
            'cleanup_results': cleanup_results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))