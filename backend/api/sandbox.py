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
from services.sandbox_service import get_sandbox_service, SandboxService
from services.strategy_ai_service import get_strategy_ai_service, StrategyAIService
from services.error_logging_service import log_critical_error
from utils.error_sanitizer import SafeHTTPException, is_development_mode
from utils.strategy_parameter_template import get_strategy_parameter_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

# Dependency functions for service injection
def get_sandbox_service_dep() -> SandboxService:
    """Dependency to inject SandboxService"""
    return get_sandbox_service()

def get_ai_service_dep() -> StrategyAIService:
    """Dependency to inject StrategyAIService"""
    return get_strategy_ai_service()

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

class BatchTestRequest(BaseModel):
    parameter_sets: List[Dict[str, Any]] = Field(..., description="List of parameter sets to test")
    max_opportunities: int = Field(10, description="Maximum opportunities per test")
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

class DeleteResponse(BaseModel):
    message: str
    deleted_id: str
    timestamp: str

class DeploymentResponse(BaseModel):
    status: str
    message: str
    config_id: str
    deployed_at: str

class ErrorResponse(BaseModel):
    error: bool
    message: str
    error_type: str
    timestamp: Optional[str] = None

class UniverseResponse(BaseModel):
    universes: Dict[str, Any]
    total_count: int

class CachedDataResponse(BaseModel):
    symbol: str
    data: Dict[str, Any]
    cached_at: str
    expires_at: str

class ParameterFieldResponse(BaseModel):
    name: str
    label: str
    type: str
    value: Any
    options: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: str = ""
    enabled: bool = True
    category: str = "general"

class ParameterSectionResponse(BaseModel):
    name: str
    label: str
    fields: List[ParameterFieldResponse]
    enabled: bool = True
    description: str = ""

class StrategyTemplateResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    sections: List[ParameterSectionResponse]

class StrategyListResponse(BaseModel):
    strategies: List[Dict[str, str]]


# Strategy Management Endpoints
@router.get("/strategies/", response_model=List[StrategyConfigResponse])
async def list_user_strategies(
    sandbox_service: SandboxService = Depends(get_sandbox_service_dep),
    user_id: str = Query("default_user", description="User identifier")
):
    """List all sandbox strategy configurations for a user"""
    try:
        configs = await sandbox_service.get_user_strategies(user_id)
        
        return [StrategyConfigResponse(**config.to_dict()) for config in configs]
        
    except Exception as e:
        error_response = SafeHTTPException.internal_error(e)
        raise HTTPException(
            status_code=500, 
            detail=error_response["message"] if not is_development_mode() else str(e)
        )


@router.post("/strategies/", response_model=StrategyConfigResponse)
async def create_strategy_config(
    request: StrategyConfigRequest,
    sandbox_service: SandboxService = Depends(get_sandbox_service_dep),
    user_id: str = Query("default_user", description="User identifier")
):
    """Create a new sandbox strategy configuration"""
    try:
        
        config = await sandbox_service.create_strategy_config(
            strategy_id=request.strategy_id,
            name=request.name,
            config_data=request.config_data,
            user_id=user_id
        )
        
        return StrategyConfigResponse(**config.to_dict())
        
    except Exception as e:
        error_response = SafeHTTPException.internal_error(e)
        raise HTTPException(
            status_code=500,
            detail=error_response["message"] if not is_development_mode() else str(e)
        )


@router.get("/strategies/{config_id}", response_model=StrategyConfigResponse)
async def get_strategy_config(
    config_id: str,
    sandbox_service: SandboxService = Depends(get_sandbox_service_dep)
):
    """Get a specific sandbox strategy configuration"""
    try:
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
        
        # Explicit 501 Not Implemented - prevents silent failures
        raise HTTPException(status_code=501, detail="Strategy deletion not implemented yet")
        
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


@router.post("/test/batch/{config_id}")
async def run_batch_parameter_test(config_id: str, batch_request: BatchTestRequest):
    """Run batch tests with different parameter combinations for optimization"""
    try:
        sandbox_service = get_sandbox_service()
        
        # Validate parameter sets
        if not batch_request.parameter_sets:
            raise HTTPException(status_code=400, detail="At least one parameter set required")
        
        if len(batch_request.parameter_sets) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 parameter sets allowed per batch")
        
        results = await sandbox_service.run_batch_parameter_test(config_id, batch_request.parameter_sets)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running batch parameter test: {e}")
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


@router.post("/test/preview/{config_id}")
async def preview_parameter_changes(config_id: str, parameter_changes: Dict[str, Any]):
    """Get quick preview of how parameter changes might affect opportunity count"""
    try:
        sandbox_service = get_sandbox_service()
        
        # Get current strategy config
        config = await sandbox_service.get_strategy_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Strategy configuration {config_id} not found")
        
        # Create preview config with changes
        preview_config_data = {**config.config_data}
        
        # Apply parameter changes
        for param_path, value in parameter_changes.items():
            keys = param_path.split('.')
            current = preview_config_data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
        
        # Quick lightweight preview (don't run full test)
        # Estimate impact based on parameter changes
        current_universe = config.config_data.get('universe', {}).get('primary_symbols', [])
        new_universe = preview_config_data.get('universe', {}).get('primary_symbols', [])
        
        # Estimate opportunity count based on universe size and trading parameters
        base_opportunities_per_symbol = 0.8  # Average baseline
        universe_size = len(new_universe)
        
        # Adjust based on key parameters
        dte_range = preview_config_data.get('trading', {}).get('target_dte_range', [7, 28])
        dte_range_size = dte_range[1] - dte_range[0] if len(dte_range) >= 2 else 21
        dte_multiplier = min(1.0, dte_range_size / 21.0)  # Longer ranges = more opportunities
        
        max_positions = preview_config_data.get('trading', {}).get('max_positions', 3)
        
        estimated_opportunities = int(universe_size * base_opportunities_per_symbol * dte_multiplier)
        estimated_opportunities = min(estimated_opportunities, max_positions * 2)  # Cap based on position limits
        
        # Compare with current config
        current_estimated = int(len(current_universe) * base_opportunities_per_symbol)
        
        preview_result = {
            'parameter_changes': parameter_changes,
            'estimated_opportunities': estimated_opportunities,
            'current_opportunities_estimate': current_estimated,
            'opportunity_change': estimated_opportunities - current_estimated,
            'universe_change': {
                'from': len(current_universe),
                'to': len(new_universe),
                'symbols_added': list(set(new_universe) - set(current_universe)),
                'symbols_removed': list(set(current_universe) - set(new_universe))
            },
            'parameter_impact': {
                'dte_range': dte_range,
                'dte_multiplier': round(dte_multiplier, 2),
                'max_positions': max_positions
            },
            'preview_timestamp': datetime.utcnow().isoformat(),
            'note': 'This is a quick estimate. Run full test for accurate results.'
        }
        
        return preview_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating parameter preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/compare/{config_id}")
async def compare_parameter_sets(
    config_id: str, 
    parameter_set_a: Dict[str, Any], 
    parameter_set_b: Dict[str, Any],
    test_name_a: str = "Configuration A",
    test_name_b: str = "Configuration B"
):
    """Run A/B comparison between two parameter sets"""
    try:
        sandbox_service = get_sandbox_service()
        
        # Run batch test with both parameter sets
        batch_request = [parameter_set_a, parameter_set_b]
        batch_results = await sandbox_service.run_batch_parameter_test(config_id, batch_request)
        
        if not batch_results.get('success') or len(batch_results.get('batch_results', [])) < 2:
            raise HTTPException(status_code=500, detail="Failed to run comparison tests")
        
        results = batch_results['batch_results']
        result_a = results[0]
        result_b = results[1]
        
        # Calculate performance differences
        def safe_get_metric(result, metric_path, default=0):
            """Safely get nested metric value"""
            try:
                parts = metric_path.split('.')
                value = result
                for part in parts:
                    value = value.get(part, {})
                return value if isinstance(value, (int, float)) else default
            except:
                return default
        
        metrics_a = result_a.get('performance_metrics', {})
        metrics_b = result_b.get('performance_metrics', {})
        
        comparison = {
            'configuration_a': {
                'name': test_name_a,
                'parameters': parameter_set_a,
                'results': result_a,
                'metrics': metrics_a
            },
            'configuration_b': {
                'name': test_name_b,
                'parameters': parameter_set_b,
                'results': result_b,
                'metrics': metrics_b
            },
            'performance_comparison': {
                'opportunities_count': {
                    'a': result_a.get('opportunities_count', 0),
                    'b': result_b.get('opportunities_count', 0),
                    'difference': result_b.get('opportunities_count', 0) - result_a.get('opportunities_count', 0),
                    'winner': 'b' if result_b.get('opportunities_count', 0) > result_a.get('opportunities_count', 0) else 'a'
                },
                'avg_probability_profit': {
                    'a': metrics_a.get('avg_probability_profit', 0),
                    'b': metrics_b.get('avg_probability_profit', 0),
                    'difference': metrics_b.get('avg_probability_profit', 0) - metrics_a.get('avg_probability_profit', 0),
                    'winner': 'b' if metrics_b.get('avg_probability_profit', 0) > metrics_a.get('avg_probability_profit', 0) else 'a'
                },
                'avg_expected_value': {
                    'a': metrics_a.get('avg_expected_value', 0),
                    'b': metrics_b.get('avg_expected_value', 0),
                    'difference': metrics_b.get('avg_expected_value', 0) - metrics_a.get('avg_expected_value', 0),
                    'winner': 'b' if metrics_b.get('avg_expected_value', 0) > metrics_a.get('avg_expected_value', 0) else 'a'
                },
                'risk_reward_ratio': {
                    'a': metrics_a.get('risk_reward_ratio', 0),
                    'b': metrics_b.get('risk_reward_ratio', 0),
                    'difference': metrics_b.get('risk_reward_ratio', 0) - metrics_a.get('risk_reward_ratio', 0),
                    'winner': 'b' if metrics_b.get('risk_reward_ratio', 0) > metrics_a.get('risk_reward_ratio', 0) else 'a'
                }
            },
            'overall_winner': None,
            'execution_time_ms': batch_results.get('execution_time_ms', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Determine overall winner based on composite score
        score_a = (metrics_a.get('avg_expected_value', 0) * metrics_a.get('avg_probability_profit', 0))
        score_b = (metrics_b.get('avg_expected_value', 0) * metrics_b.get('avg_probability_profit', 0))
        
        comparison['overall_winner'] = 'b' if score_b > score_a else 'a'
        comparison['scores'] = {'a': score_a, 'b': score_b}
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running parameter comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Assistant Endpoints
@router.post("/ai/chat/{config_id}", response_model=AIMessageResponse)
async def chat_with_ai_assistant(
    config_id: str,
    request: AIMessageRequest,
    sandbox_service: SandboxService = Depends(get_sandbox_service_dep),
    ai_service: StrategyAIService = Depends(get_ai_service_dep)
):
    """Send a message to the AI assistant for strategy analysis"""
    try:
        
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
            # Note: Conversation saving to database not yet implemented
            # Currently conversations are kept in memory only
            logger.info(f"AI conversation for {config_id} completed successfully but not persisted to database")
        
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
        # Explicit 501 Not Implemented - prevents silent failures  
        raise HTTPException(status_code=501, detail="AI chat history retrieval not implemented yet")
        
    except Exception as e:
        logger.error(f"Error getting AI chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoints removed - AI service is now working correctly

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
        
        # Explicit 501 Not Implemented - deployment is critical and must be implemented properly
        raise HTTPException(
            status_code=501, 
            detail="Strategy deployment not implemented yet. Requires: validation, format conversion, live system registration."
        )
        
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
        # Explicit 501 Not Implemented - prevents silent failures
        raise HTTPException(status_code=501, detail="Cached market data retrieval not implemented yet")
        
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/universes", response_model=UniverseResponse)
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
                'description': 'High-volume stocks / ETFs for theta strategies',
                'symbol_type': 'Mixed',
                'typical_count': 13
            },
            'sector_leaders': {
                'name': 'Sector Leaders',
                'description': 'Leading stocks by sector',
                'symbol_type': 'Mixed',
                'typical_count': 28
            }
        }
        
        return UniverseResponse(
            universes=universe_info,
            total_count=len(universe_info)
        )
        
    except Exception as e:
        logger.error(f"Error listing universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/universe/{universe_name}")
async def get_universe_symbols(universe_name: str):
    """Get symbols from a trading universe"""
    try:
        from services.universe_loader import get_universe_loader
        
        universe_loader = get_universe_loader()
        
        # Map universe names to actual loaded universe names (without .txt extension)
        universe_names = {
            'mag7': 'mag7',
            'etfs': 'etfs', 
            'top20': 'top20',
            'sector_leaders': 'sector_leaders',
            'thetacrop': 'thetacrop_symbols'  # This maps to thetacrop_symbols.txt file
        }
        
        if universe_name not in universe_names:
            raise HTTPException(status_code=404, detail=f"Universe {universe_name} not found")
        
        # Load actual symbols from universe loader
        try:
            actual_universe_name = universe_names[universe_name]
            symbols = universe_loader.get_universe(actual_universe_name)
            logger.info(f"Successfully loaded universe '{universe_name}' from file: {len(symbols)} symbols")
        except Exception as e:
            # Log critical error to database
            await log_critical_error(
                error_type="universe_loading_failed",
                message=f"Failed to load universe '{universe_name}' from universe loader: {str(e)}",
                details={
                    "universe_name": universe_name,
                    "actual_universe_name": actual_universe_name,
                    "error": str(e)
                }
            )
            logger.error(f"CRITICAL: Failed to load universe '{actual_universe_name}': {e}")
            
            # Return error instead of fallback - this forces proper universe file setup
            raise HTTPException(
                status_code=500, 
                detail=f"Universe '{universe_name}' could not be loaded from universe loader. Error: {str(e)}"
            )
        
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


# Error Monitoring Endpoints
@router.get("/errors/critical")
async def get_critical_errors(
    limit: int = Query(50, description="Maximum number of errors to return"),
    error_type: str = Query(None, description="Filter by error type"),
    unresolved_only: bool = Query(False, description="Only show unresolved errors")
):
    """Get critical system errors for monitoring"""
    try:
        from services.error_logging_service import get_critical_errors
        
        errors = await get_critical_errors(
            limit=limit,
            error_type=error_type,
            unresolved_only=unresolved_only,
            since_hours=24  # Last 24 hours
        )
        
        return {
            'errors': errors,
            'count': len(errors),
            'retrieved_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting critical errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/dashboard")
async def get_system_health_dashboard():
    """Get comprehensive system health dashboard"""
    try:
        from services.error_logging_service import get_system_health_dashboard
        
        dashboard = await get_system_health_dashboard()
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting health dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/errors/{error_id}/resolve")
async def resolve_critical_error(error_id: str, resolution_notes: str = None):
    """Mark a critical error as resolved"""
    try:
        from services.error_logging_service import mark_error_resolved
        
        success = await mark_error_resolved(error_id, resolution_notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {
            'status': 'resolved',
            'error_id': error_id,
            'resolved_at': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving critical error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/ai-service")
async def debug_ai_service():
    """Debug AI service configuration"""
    try:
        import os
        ai_service = get_strategy_ai_service()
        
        # Check if AsyncOpenAI is available
        try:
            from openai import AsyncOpenAI
            openai_import_ok = True
            openai_error = None
        except Exception as e:
            openai_import_ok = False
            openai_error = str(e)
        
        return {
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "api_key_length": len(os.getenv("OPENAI_API_KEY", "")),
            "service_enabled": ai_service.enabled,
            "client_available": ai_service.client is not None,
            "current_model": ai_service.current_model,
            "openai_library_available": ai_service.client.__class__.__name__ if ai_service.client else "No client",
            "openai_import_ok": openai_import_ok,
            "openai_import_error": openai_error
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/debug/reinit-ai-service")
async def reinitialize_ai_service():
    """Force reinitialize AI service"""
    try:
        import os
        from services.strategy_ai_service import initialize_strategy_ai_service
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "No OpenAI API key found in environment"}
        
        # Force reinitialize
        ai_service = initialize_strategy_ai_service(api_key)
        
        return {
            "status": "reinitialized",
            "enabled": ai_service.enabled,
            "client_available": ai_service.client is not None,
            "model": ai_service.current_model
        }
    except Exception as e:
        return {"error": str(e)}


# Strategy Parameter Template Endpoints
@router.get("/strategies/available", response_model=StrategyListResponse)
async def get_available_strategies():
    """Get list of available strategies with their basic info"""
    try:
        template_service = get_strategy_parameter_template()
        strategies = template_service.get_strategy_list()
        
        return StrategyListResponse(strategies=strategies)
        
    except Exception as e:
        error_response = SafeHTTPException.internal_error(e)
        raise HTTPException(
            status_code=500,
            detail=error_response["message"] if not is_development_mode() else str(e)
        )


@router.get("/strategies/{strategy_id}/template", response_model=StrategyTemplateResponse)
async def get_strategy_parameter_template_endpoint(strategy_id: str):
    """Get parameter template for a specific strategy"""
    try:
        template_service = get_strategy_parameter_template()
        template = template_service.create_template_for_strategy(strategy_id)
        
        # Convert to response model
        sections = []
        for section in template['sections']:
            fields = []
            for field in section.fields:
                fields.append(ParameterFieldResponse(
                    name=field.name,
                    label=field.label,
                    type=field.type,
                    value=field.value,
                    options=field.options,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    step=field.step,
                    description=field.description,
                    enabled=field.enabled,
                    category=field.category
                ))
            
            sections.append(ParameterSectionResponse(
                name=section.name,
                label=section.label,
                fields=fields,
                enabled=section.enabled,
                description=section.description
            ))
        
        return StrategyTemplateResponse(
            strategy_id=template['strategy_id'],
            strategy_name=template['strategy_name'],
            sections=sections
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = SafeHTTPException.internal_error(e)
        raise HTTPException(
            status_code=500,
            detail=error_response["message"] if not is_development_mode() else str(e)
        )


@router.post("/maintenance/sync-from-json")
async def sync_sandbox_from_json_strategies():
    """Sync sandbox strategies with JSON configuration files"""
    try:
        from pathlib import Path
        import json
        from services.universe_loader import get_universe_loader
        
        # Get paths
        backend_dir = Path(__file__).parent.parent
        strategies_dir = backend_dir / "config" / "strategies" / "development"
        
        if not strategies_dir.exists():
            return {"error": f"Strategies directory not found: {strategies_dir}"}
        
        sandbox_service = get_sandbox_service()
        universe_loader = get_universe_loader()
        
        results = []
        
        # Load each JSON strategy file
        for json_file in strategies_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    strategy_config = json.load(f)
                
                strategy_name = strategy_config.get("strategy_name", json_file.stem)
                strategy_id = strategy_config.get("strategy_type", json_file.stem.lower())
                
                # Convert JSON config to sandbox format
                sandbox_config = convert_json_to_sandbox_config(strategy_config, universe_loader)
                
                # Check if sandbox strategy already exists
                existing_strategies = await sandbox_service.get_user_strategies()
                existing_strategy = next((s for s in existing_strategies if s.name == strategy_name), None)
                
                if existing_strategy:
                    # Update existing strategy
                    updated_config = await sandbox_service.update_strategy_config(
                        existing_strategy.id,
                        {"config_data": sandbox_config}
                    )
                    results.append({
                        "file": json_file.name,
                        "strategy": strategy_name,
                        "action": "updated",
                        "id": existing_strategy.id,
                        "universe_symbols": len(sandbox_config.get("universe", {}).get("primary_symbols", []))
                    })
                else:
                    # Create new sandbox strategy
                    config = await sandbox_service.create_strategy_config(
                        strategy_id=strategy_id,
                        name=strategy_name,
                        config_data=sandbox_config,
                        user_id="default_user"
                    )
                    results.append({
                        "file": json_file.name,
                        "strategy": strategy_name,
                        "action": "created",
                        "id": config.id,
                        "universe_symbols": len(sandbox_config.get("universe", {}).get("primary_symbols", []))
                    })
                    
            except Exception as e:
                results.append({
                    "file": json_file.name,
                    "error": str(e),
                    "action": "failed"
                })
        
        return {
            "status": "completed",
            "processed_files": len([r for r in results if "error" not in r]),
            "failed_files": len([r for r in results if "error" in r]),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
                
    except Exception as e:
        logger.error(f"Error syncing sandbox from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def convert_json_to_sandbox_config(json_config: Dict[str, Any], universe_loader) -> Dict[str, Any]:
    """Convert JSON strategy configuration to sandbox format"""
    sandbox_config = {}
    
    # Handle universe configuration
    universe_config = json_config.get("universe", {})
    if universe_config:
        symbols = []
        
        if "universe_file" in universe_config:
            universe_file = Path(universe_config["universe_file"]).stem
            try:
                symbols = universe_loader.get_universe(universe_file)
                logger.info(f"Loaded {len(symbols)} symbols from universe file: {universe_file}")
            except Exception as e:
                logger.warning(f"Failed to load universe from file {universe_file}: {e}")
        
        elif "universe_name" in universe_config:
            universe_name = universe_config["universe_name"]
            try:
                symbols = universe_loader.get_universe(universe_name)
                logger.info(f"Loaded {len(symbols)} symbols from universe: {universe_name}")
            except Exception as e:
                logger.warning(f"Failed to load universe {universe_name}: {e}")
        
        if not symbols:
            symbols = universe_loader.get_universe("thetacrop_symbols") or ["SPY", "QQQ", "IWM"]
        
        sandbox_config["universe"] = {
            "primary_symbols": symbols,
            "universe_name": universe_config.get("universe_name", "custom"),
            "symbol_type": universe_config.get("symbol_type", "Mixed")
        }
    
    # Handle position parameters
    position_params = json_config.get("position_parameters", {})
    if position_params:
        # Handle complex DTE range (list of specific days)
        dte_range = position_params.get("target_dte_range", [7, 28])
        if isinstance(dte_range, list) and len(dte_range) > 2:
            # Convert [5,6,7,8,9,10] to [5, 10] (min, max)
            dte_range = [min(dte_range), max(dte_range)]
        
        sandbox_config["trading"] = {
            "target_dte_range": dte_range,
            "delta_target": position_params.get("delta_target", 0.15),
            "max_positions": position_params.get("max_positions", 3),
            "wing_widths": position_params.get("wing_widths", [5, 10, 15])
        }
    
    # Handle risk management
    exit_rules = json_config.get("exit_rules", {})
    if exit_rules:
        profit_targets = exit_rules.get("profit_targets", [])
        stop_losses = exit_rules.get("stop_loss_rules", [])
        
        profit_target = 0.50
        loss_limit = 2.00
        
        if profit_targets:
            profit_target = profit_targets[0].get("level", 0.50)
        if stop_losses:
            loss_limit = abs(stop_losses[0].get("trigger", -0.30)) * 3
        
        sandbox_config["risk"] = {
            "profit_target": profit_target,
            "loss_limit": loss_limit
        }
    
    # Include strategy metadata
    sandbox_config["strategy"] = {
        "id": json_config.get("strategy_type", "unknown"),
        "name": json_config.get("strategy_name", "Unknown Strategy"),
        "description": json_config.get("description", "")
    }
    
    return sandbox_config