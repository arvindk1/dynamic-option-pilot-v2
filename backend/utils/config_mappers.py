"""
Configuration Mappers
Utilities for converting between different strategy configuration formats
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from services.universe_loader import get_universe_loader

logger = logging.getLogger(__name__)


def convert_json_to_sandbox_config(
    json_config: Dict[str, Any], universe_loader=None
) -> Dict[str, Any]:
    """
    Convert JSON strategy configuration to sandbox format

    Args:
        json_config: Strategy configuration from JSON file
        universe_loader: Universe loader service instance

    Returns:
        Dict formatted for sandbox system

    Raises:
        RuntimeError: If universe loading fails (no fallbacks)
    """
    if universe_loader is None:
        universe_loader = get_universe_loader()

    sandbox_config = {}

    # Handle universe configuration - strict error on failure
    universe_config = json_config.get("universe", {})
    if universe_config:
        symbols = []

        if "universe_file" in universe_config:
            # Extract universe name from file path
            universe_file = Path(universe_config["universe_file"]).stem
            try:
                symbols = universe_loader.get_universe(universe_file)
                logger.info(
                    f"Loaded {len(symbols)} symbols from universe file: {universe_file}"
                )
            except Exception as e:
                logger.error(f"Failed to load universe from file {universe_file}: {e}")
                raise RuntimeError(
                    f"Universe file '{universe_file}' could not be loaded: {e}"
                )

        elif "universe_name" in universe_config:
            # Use universe name directly
            universe_name = universe_config["universe_name"]
            try:
                symbols = universe_loader.get_universe(universe_name)
                logger.info(
                    f"Loaded {len(symbols)} symbols from universe: {universe_name}"
                )
            except Exception as e:
                logger.error(f"Failed to load universe {universe_name}: {e}")
                raise RuntimeError(
                    f"Universe '{universe_name}' could not be loaded: {e}"
                )

        # NO FALLBACK - explicit error if no symbols loaded
        if not symbols:
            raise RuntimeError(
                "No symbols loaded from universe configuration - system health compromised"
            )

        sandbox_config["universe"] = {
            "primary_symbols": symbols,
            "universe_name": universe_config.get("universe_name", "custom"),
            "symbol_type": universe_config.get("symbol_type", "Mixed"),
            "max_symbols": universe_config.get("max_symbols", len(symbols)),
        }

    # Handle position parameters
    position_params = json_config.get("position_parameters", {})
    if position_params:
        sandbox_config["trading"] = {
            "target_dte_range": position_params.get("target_dte_range", [7, 28]),
            "delta_target": position_params.get("delta_target", 0.15),
            "max_positions": position_params.get("max_positions", 3),
            "wing_widths": position_params.get("wing_widths", [5, 10, 15]),
        }

    # Handle risk management
    exit_rules = json_config.get("exit_rules", {})
    if exit_rules:
        profit_targets = exit_rules.get("profit_targets", [])
        stop_losses = exit_rules.get("stop_loss_rules", [])

        profit_target = 0.50  # Default
        loss_limit = 2.00  # Default

        if profit_targets:
            profit_target = profit_targets[0].get("level", 0.50)

        if stop_losses:
            loss_limit = (
                abs(stop_losses[0].get("trigger", -0.30)) * 3
            )  # Convert to multiplier

        sandbox_config["risk"] = {
            "profit_target": profit_target,
            "loss_limit": loss_limit,
        }

    # Handle scoring/optimization parameters
    scoring = json_config.get("scoring", {})
    if scoring:
        sandbox_config["scoring"] = {
            "base_probability_weight": scoring.get("base_probability_weight", 4.0),
            "score_ceiling": scoring.get("score_ceiling", 10.0),
            "score_floor": scoring.get("score_floor", 1.0),
        }

    # Include original strategy metadata
    sandbox_config["strategy"] = {
        "id": json_config.get("strategy_type", "unknown"),
        "name": json_config.get("strategy_name", "Unknown Strategy"),
        "description": json_config.get("description", ""),
        "risk_level": json_config.get("educational_content", {}).get(
            "risk_level", "MEDIUM"
        ),
    }

    return sandbox_config


def convert_sandbox_to_json_config(sandbox_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert sandbox configuration back to JSON strategy format

    Args:
        sandbox_config: Configuration from sandbox system

    Returns:
        Dict formatted for JSON strategy files
    """
    json_config = {}

    # Extract strategy metadata
    strategy_info = sandbox_config.get("strategy", {})
    json_config["strategy_type"] = strategy_info.get("id", "unknown")
    json_config["strategy_name"] = strategy_info.get("name", "Unknown Strategy")
    json_config["description"] = strategy_info.get("description", "")

    # Convert universe configuration
    universe_info = sandbox_config.get("universe", {})
    if universe_info:
        json_config["universe"] = {
            "universe_name": universe_info.get("universe_name", "custom"),
            "symbol_type": universe_info.get("symbol_type", "Mixed"),
            "primary_symbols": universe_info.get("primary_symbols", []),
            "max_symbols": universe_info.get("max_symbols", 50),
        }

    # Convert trading parameters
    trading_info = sandbox_config.get("trading", {})
    if trading_info:
        json_config["position_parameters"] = {
            "target_dte_range": trading_info.get("target_dte_range", [7, 28]),
            "delta_target": trading_info.get("delta_target", 0.15),
            "max_positions": trading_info.get("max_positions", 3),
            "wing_widths": trading_info.get("wing_widths", [5, 10, 15]),
        }

    # Convert risk management
    risk_info = sandbox_config.get("risk", {})
    if risk_info:
        json_config["exit_rules"] = {
            "profit_targets": [{"level": risk_info.get("profit_target", 0.50)}],
            "stop_loss_rules": [{"trigger": -risk_info.get("loss_limit", 2.00) / 3}],
        }

    # Convert scoring parameters
    scoring_info = sandbox_config.get("scoring", {})
    if scoring_info:
        json_config["scoring"] = {
            "base_probability_weight": scoring_info.get("base_probability_weight", 4.0),
            "score_ceiling": scoring_info.get("score_ceiling", 10.0),
            "score_floor": scoring_info.get("score_floor", 1.0),
        }

    # Add educational content
    json_config["educational_content"] = {
        "risk_level": strategy_info.get("risk_level", "MEDIUM"),
        "best_for": "Configurable via sandbox system",
    }

    return json_config


def validate_strategy_config(
    config: Dict[str, Any], config_type: str = "sandbox"
) -> Dict[str, Any]:
    """
    Validate strategy configuration and return validation results

    Args:
        config: Strategy configuration to validate
        config_type: Type of config ("sandbox" or "json")

    Returns:
        Dict with validation results
    """
    validation_result = {"valid": True, "errors": [], "warnings": []}

    if config_type == "sandbox":
        # Validate sandbox configuration
        if "universe" not in config:
            validation_result["errors"].append("Missing universe configuration")
            validation_result["valid"] = False

        universe_config = config.get("universe", {})
        symbols = universe_config.get("primary_symbols", [])
        if not symbols:
            validation_result["errors"].append("No symbols in universe configuration")
            validation_result["valid"] = False
        elif len(symbols) < 3:
            validation_result["warnings"].append(
                f"Only {len(symbols)} symbols in universe - consider adding more for diversification"
            )

        # Validate trading parameters
        trading_config = config.get("trading", {})
        dte_range = trading_config.get("target_dte_range", [])
        if len(dte_range) != 2 or dte_range[0] >= dte_range[1]:
            validation_result["errors"].append(
                "Invalid DTE range - should be [min, max] with min < max"
            )
            validation_result["valid"] = False

    elif config_type == "json":
        # Validate JSON configuration
        required_fields = ["strategy_name", "strategy_type"]
        for field in required_fields:
            if field not in config:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

    return validation_result
