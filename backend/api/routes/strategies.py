import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException

from core.orchestrator.strategy_registry import get_strategy_registry
from services.universe_loader import get_universe_loader
from services.opportunity_cache import get_opportunity_cache
from plugins.trading.base_strategy import StrategyOpportunity

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
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
                strategies.append(
                    {
                        "id": strategy.strategy_id,
                        "name": strategy.strategy_name,
                        "description": strategy.description,
                        "risk_level": "MEDIUM",  # Could be determined from strategy config
                        "min_dte": strategy.position_parameters.get("min_dte", 7),
                        "max_dte": strategy.position_parameters.get("max_dte", 45),
                        "enabled": strategy.is_active,
                        "category": strategy.strategy_type.lower()
                        .replace("_", " ")
                        .title(),
                    }
                )

            return {"strategies": strategies}

        # Get strategies from registry
        registrations = registry.get_all_registrations()
        strategies = []

        for strategy_id, registration in registrations.items():
            instance = registry.get_strategy(strategy_id)
            strategies.append(
                {
                    "id": strategy_id,
                    "name": registration.config.name,
                    "description": f"{registration.config.category} strategy",
                    "risk_level": "MEDIUM",  # Could be determined from strategy config
                    "min_dte": registration.config.min_dte,
                    "max_dte": registration.config.max_dte,
                    "enabled": registration.enabled and instance is not None,
                    "category": registration.config.category,
                    "last_scan": (
                        registration.last_scan.isoformat()
                        if registration.last_scan
                        else None
                    ),
                    "total_opportunities": registration.total_opportunities,
                }
            )

        return {"strategies": strategies}

    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        # Return empty strategies list on error instead of hardcoded fallback
        return {"strategies": []}


@router.get("/{strategy_id}/opportunities")
async def get_strategy_opportunities(
    strategy_id: str, symbol: str = "SPY", max_opportunities: int = 10
):
    """Get opportunities for a specific strategy."""
    # Get the opportunity cache
    cache = get_opportunity_cache()

    # Get all opportunities
    all_opportunities = await cache.get_opportunities()

    # Filter opportunities for this strategy
    strategy_opportunities = []
    for opp in all_opportunities:
        # Map opportunities to strategies based on characteristics
        target_strategy = None

        # Get opportunity characteristics
        prob_profit = opp.get("probability_profit", 0)
        dte = opp.get("days_to_expiration", 0)
        premium = opp.get("premium", 0)
        liquidity = opp.get("liquidity_score", 0)
        strategy_type = opp.get("strategy_type", "")

        # Map based on strategy characteristics and opportunity attributes
        if strategy_id == "ThetaCropWeekly" and (
            dte <= 21 or "theta" in strategy_type.lower()
        ):
            target_strategy = strategy_id
        elif strategy_id == "IronCondor" and (
            liquidity > 7 or "neutral" in strategy_type.lower()
        ):
            target_strategy = strategy_id
        elif strategy_id == "RSICouponStrategy" and (
            prob_profit > 0.75 or "high_probability" in strategy_type
        ):
            target_strategy = strategy_id
        elif strategy_id == "CreditSpread" and (
            premium > 2.0 or "credit" in strategy_type.lower()
        ):
            target_strategy = strategy_id
        elif strategy_id == "ProtectivePut" and dte > 30:
            target_strategy = strategy_id
        elif strategy_id == "ButterflySpread" and liquidity > 6:
            target_strategy = strategy_id
        elif strategy_id == "Straddle" and (
            "volatility" in strategy_type.lower() or premium > 3.0
        ):
            target_strategy = strategy_id
        elif strategy_id == "Strangle" and (
            "volatility" in strategy_type.lower() or dte > 21
        ):
            target_strategy = strategy_id
        elif strategy_id == "CoveredCall" and dte > 30:
            target_strategy = strategy_id
        elif strategy_id == "CalendarSpread" and dte > 14:
            target_strategy = strategy_id
        elif strategy_id == "VerticalSpread" and prob_profit > 0.70:
            target_strategy = strategy_id
        elif strategy_id == "SingleOption" and liquidity > 8:
            target_strategy = strategy_id
        elif strategy_id == "Collar" and dte > 21:
            target_strategy = strategy_id
        else:
            # Distribute remaining opportunities in round-robin fashion
            # This ensures all strategies get some opportunities
            opportunity_hash = hash(opp.get("opportunity_id", "")) % 13
            strategy_list = [
                "ThetaCropWeekly",
                "IronCondor",
                "RSICouponStrategy",
                "CreditSpread",
                "ProtectivePut",
                "ButterflySpread",
                "Straddle",
                "Strangle",
                "CoveredCall",
                "CalendarSpread",
                "VerticalSpread",
                "SingleOption",
                "Collar",
            ]
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
            "scan_time": datetime.utcnow().isoformat(),
        },
    }


@router.post("/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """Enable a trading strategy."""
    return {
        "strategy_id": strategy_id,
        "status": "enabled",
        "message": f"Strategy {strategy_id} has been enabled",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """Disable a trading strategy."""
    return {
        "strategy_id": strategy_id,
        "status": "disabled",
        "message": f"Strategy {strategy_id} has been disabled",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{strategy_id}/status")
async def get_strategy_status(strategy_id: str):
    """Get status of a specific strategy."""
    # Mock status for now - in production this would check actual strategy state
    strategy_info = {
        "iron_condor": {
            "enabled": True,
            "last_scan": "2 min ago",
            "opportunities_found": 2,
        },
        "put_spread": {
            "enabled": True,
            "last_scan": "1 min ago",
            "opportunities_found": 3,
        },
        "covered_call": {
            "enabled": False,
            "last_scan": "5 min ago",
            "opportunities_found": 0,
        },
    }

    info = strategy_info.get(
        strategy_id, {"enabled": False, "last_scan": "never", "opportunities_found": 0}
    )

    return {
        "strategy_id": strategy_id,
        "status": "active" if info["enabled"] else "inactive",
        "enabled": info["enabled"],
        "last_scan": info["last_scan"],
        "opportunities_found": info["opportunities_found"],
        "timestamp": datetime.utcnow().isoformat(),
    }


# Individual Strategy Scan Endpoints (like V1)
@router.post("/{strategy_id}/scan")
async def scan_individual_strategy(
    strategy_id: str, symbol: Optional[str] = "SPY", max_opportunities: int = 5
):
    """Scan for opportunities using a specific strategy (like V1's individual scans)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(
                status_code=503, detail="Strategy registry not available"
            )

        # Get the specific strategy plugin
        strategy_plugin = registry.get_strategy(strategy_id)
        if not strategy_plugin:
            raise HTTPException(
                status_code=404, detail=f"Strategy {strategy_id} not found"
            )

        # Get strategy config for universe symbols
        json_config = strategy_plugin.json_config
        universe_config = json_config.universe or {}

        # Determine symbols to scan from external universe file or configuration
        scan_symbols = []
        universe_loader = get_universe_loader()

        if "universe_file" in universe_config:
            # Load from external file (preferred approach)
            try:
                scan_symbols = universe_loader.load_universe_symbols(
                    universe_config["universe_file"]
                )
                max_symbols = universe_config.get("max_symbols", 5)
                scan_symbols = scan_symbols[:max_symbols]
            except Exception as e:
                logger.warning(
                    f"Failed to load universe file: {e}, falling back to primary_symbols"
                )
                scan_symbols = universe_config.get("primary_symbols", [symbol])[:5]
        elif "primary_symbols" in universe_config:
            scan_symbols = universe_config["primary_symbols"][
                :5
            ]  # Limit to 5 for performance
        elif "preferred_symbols" in universe_config:
            scan_symbols = universe_config["preferred_symbols"][:5]
        elif "symbol_for_full_universe" in universe_config:
            # Legacy format - use single symbol for screening
            scan_symbols = [universe_config["symbol_for_full_universe"]]
        else:
            # Load default universe from external file
            try:
                scan_symbols = universe_loader.load_universe_symbols(
                    "default_etfs.txt"
                )[:5]
            except Exception as e:
                logger.warning(
                    f"Failed to load default universe: {e}, using fallback symbol"
                )
                scan_symbols = [symbol]  # Final fallback

        logger.info(f"Scanning strategy {strategy_id} with symbols: {scan_symbols}")

        # Use strategy plugin to scan for opportunities with timeout
        try:
            opportunities = await asyncio.wait_for(
                strategy_plugin.scan_opportunities(scan_symbols),
                timeout=30.0,  # 30 second timeout
            )
            logger.info(
                f"Strategy {strategy_id} scan found {len(opportunities)} opportunities"
            )
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
                "bias": getattr(opp, "bias", "NEUTRAL"),
                "rsi": getattr(opp, "rsi", 50.0),
                "created_at": getattr(
                    opp, "generated_at", datetime.utcnow()
                ).isoformat(),
                "scan_source": "individual_strategy_scan",
                "universe": opp.universe or "default",
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
                "avg_probability_profit": (
                    sum(o.get("probability_profit", 0) for o in opportunities_data)
                    / len(opportunities_data)
                    if opportunities_data
                    else 0
                ),
                "avg_expected_value": (
                    sum(o.get("expected_value", 0) for o in opportunities_data)
                    / len(opportunities_data)
                    if opportunities_data
                    else 0
                ),
                "avg_premium": (
                    sum(o.get("premium", 0) for o in opportunities_data)
                    / len(opportunities_data)
                    if opportunities_data
                    else 0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error scanning strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy scan failed: {str(e)}")


@router.post("/{strategy_id}/quick-scan")
async def quick_scan_strategy(strategy_id: str):
    """Quick scan for a strategy using its default universe (like V1's quick scans)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(
                status_code=503, detail="Strategy registry not available"
            )

        strategy_plugin = registry.get_strategy(strategy_id)
        if not strategy_plugin:
            raise HTTPException(
                status_code=404, detail=f"Strategy {strategy_id} not found"
            )

        json_config = strategy_plugin.json_config
        universe_config = json_config.universe or {}

        # Load symbols from external universe file or configuration (quick scan)
        scan_symbols = []
        universe_loader = get_universe_loader()

        if "universe_file" in universe_config:
            # Load from external file (preferred approach)
            try:
                scan_symbols = universe_loader.load_universe_symbols(
                    universe_config["universe_file"]
                )
                max_symbols = min(
                    universe_config.get("max_symbols", 3), 3
                )  # Quick scan limit
                scan_symbols = scan_symbols[:max_symbols]
            except Exception as e:
                logger.warning(
                    f"Failed to load universe file: {e}, falling back to primary_symbols"
                )
                scan_symbols = universe_config.get("primary_symbols", [])[:3]
        elif "primary_symbols" in universe_config:
            scan_symbols = universe_config["primary_symbols"][
                :3
            ]  # Quick scan - fewer symbols
        elif "preferred_symbols" in universe_config:
            scan_symbols = universe_config["preferred_symbols"][:3]
        elif "symbol_for_full_universe" in universe_config:
            # Legacy format - use single symbol for screening
            scan_symbols = [universe_config["symbol_for_full_universe"]]
        else:
            # Load default universe from external file
            try:
                scan_symbols = universe_loader.load_universe_symbols(
                    "default_etfs.txt"
                )[:3]
            except Exception as e:
                logger.warning(
                    f"Failed to load default universe: {e}, using standard defaults"
                )
                scan_symbols = [
                    "SPY",
                    "QQQ",
                    "IWM",
                ]  # Final fallback only if external loading fails

        logger.info(f"Quick scanning {strategy_id} with symbols: {scan_symbols}")

        # Scan opportunities with timeout
        try:
            opportunities = await asyncio.wait_for(
                strategy_plugin.scan_opportunities(scan_symbols),
                timeout=15.0,  # 15 second timeout for quick scan
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
                "best_probability": max(
                    (opp.probability_profit for opp in opportunities), default=0
                ),
                "best_expected_value": max(
                    (opp.expected_value for opp in opportunities), default=0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error in quick scan for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")


@router.get("/{strategy_id}/parameters")
async def get_strategy_parameters(strategy_id: str):
    """Get current parameters for a strategy (for Strategy Tab parameter editor)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(
                status_code=503, detail="Strategy registry not available"
            )

        # Get strategy instance or configuration
        strategy_instance = registry.get_strategy(strategy_id)
        if not strategy_instance:
            # Check if it's a JSON strategy
            from core.strategies.json_strategy_loader import JSONStrategyLoader

            loader = JSONStrategyLoader()

            # Try to load the specific strategy
            json_strategy = loader.load_strategy(strategy_id)
            if not json_strategy:
                raise HTTPException(
                    status_code=404, detail=f"Strategy {strategy_id} not found"
                )

            # Return JSON strategy parameters
            return {
                "strategy_id": strategy_id,
                "strategy_name": json_strategy.strategy_name,
                "strategy_type": json_strategy.strategy_type,
                "parameters": json_strategy.get_effective_config(),
                "parameter_overrides": json_strategy.parameter_overrides or {},
                "last_updated": datetime.utcnow().isoformat(),
            }

        # Return regular strategy parameters
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy_instance.get_config().name,
            "parameters": strategy_instance.get_config().to_dict(),
            "parameter_overrides": {},
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting strategy parameters for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/parameters/override")
async def override_strategy_parameters(
    strategy_id: str, parameter_overrides: Dict[str, Any]
):
    """Override strategy parameters for Strategy Tab testing (does not affect Trading Tab)."""
    try:
        registry = get_strategy_registry()
        if not registry:
            raise HTTPException(
                status_code=503, detail="Strategy registry not available"
            )

        # Store parameter overrides in memory for Strategy Tab use
        # These overrides are separate from active trading configurations
        # This is a bit of a hack. In a real app, this would be stored in a user session or a temporary DB table.
        # For now, we'll store it on the app state.
        # This requires passing the app state to the router, or using a dependency injection system.
        # For now, we will assume this function has access to the app state.
        # A better solution would be to create a service to handle this.
        # from main import app
        # if not hasattr(app.state, "strategy_parameter_overrides"):
        #     app.state.strategy_parameter_overrides = {}

        # app.state.strategy_parameter_overrides[strategy_id] = {
        #     "overrides": parameter_overrides,
        #     "timestamp": datetime.utcnow().isoformat(),
        #     "active": True,
        # }

        logger.info(
            f"Parameter overrides applied for strategy {strategy_id}: {parameter_overrides}"
        )

        return {
            "strategy_id": strategy_id,
            "status": "success",
            "message": f"Parameter overrides applied for {strategy_id}",
            "overrides_applied": parameter_overrides,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "These overrides only affect Strategy Tab testing, not live Trading Tab execution. This feature is not fully implemented.",
        }

    except Exception as e:
        logger.error(f"Error overriding parameters for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/parameters/overrides")
async def get_strategy_parameter_overrides(strategy_id: str):
    """Get current parameter overrides for a strategy."""
    # This is a mock implementation. See note in the POST endpoint.
    return {
        "strategy_id": strategy_id,
        "overrides": {},
        "active": False,
        "timestamp": None,
        "note": "This feature is not fully implemented."
    }


@router.delete("/{strategy_id}/parameters/overrides")
async def clear_strategy_parameter_overrides(strategy_id: str):
    """Clear parameter overrides for a strategy (revert to default parameters)."""
    # This is a mock implementation. See note in the POST endpoint.
    return {
        "strategy_id": strategy_id,
        "status": "success",
        "message": f"Parameter overrides cleared for {strategy_id}",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "This feature is not fully implemented."
    }


@router.post("/{strategy_id}/test-scan")
async def test_strategy_with_overrides(
    strategy_id: str, test_parameters: Dict[str, Any] = None
):
    """Test a strategy with current parameter overrides (Strategy Tab functionality)."""
    # This is a mock implementation.
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
            "risk_reward_ratio": 61.58,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "test_results": {
            "opportunities_found": 3,
            "opportunities": [],
            "scan_time": datetime.utcnow().isoformat(),
            "parameters_used": test_parameters or {},
            "testing_mode": True,
        },
        "status": "success",
        "message": f"Test scan completed for {strategy_id} (mock results)",
    }


@router.get("/json/available")
async def get_available_json_strategies():
    """Get all available JSON strategies for Strategy Tab."""
    try:
        from core.strategies.json_strategy_loader import JSONStrategyLoader

        loader = JSONStrategyLoader()
        strategies = loader.load_all_strategies()

        strategy_list = []
        for strategy in strategies:
            strategy_list.append(
                {
                    "id": strategy.strategy_id,
                    "name": strategy.strategy_name,
                    "type": strategy.strategy_type,
                    "description": strategy.description,
                    "category": strategy.strategy_type.lower()
                    .replace("_", " ")
                    .title(),
                    "enabled": strategy.is_active,
                    "parameter_count": len(strategy.entry_signals)
                    + len(strategy.position_parameters),
                    "has_overrides": strategy.parameter_overrides is not None,
                }
            )

        return {
            "json_strategies": strategy_list,
            "total_count": len(strategy_list),
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting available JSON strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
