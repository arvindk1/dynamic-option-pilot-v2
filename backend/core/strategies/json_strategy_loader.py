"""
JSON Strategy Loader
===================
Load and validate JSON strategy configurations from the rules directory.
Supports both Strategy Tab (testing) and Trading Tab (live execution).
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class StrategyValidationResult:
    """Result of strategy validation."""

    is_valid: bool
    strategy_id: str
    errors: List[str]
    warnings: List[str]


@dataclass
class JSONStrategyConfig:
    """Structured representation of a JSON strategy configuration."""

    strategy_id: str
    strategy_name: str
    strategy_type: str
    description: str
    module: str

    # Core parameters
    position_parameters: Dict[str, Any]
    entry_signals: Dict[str, Any]
    exit_rules: Dict[str, Any]
    scoring: Dict[str, Any]
    risk_management: Dict[str, Any]

    # Optional parameters
    universe: Optional[Dict[str, Any]] = None
    timing: Optional[Dict[str, Any]] = None
    strike_selection: Optional[Dict[str, Any]] = None
    educational_content: Optional[Dict[str, Any]] = None

    # Runtime overrides (for Strategy Tab testing)
    parameter_overrides: Optional[Dict[str, Any]] = None
    is_active: bool = True
    last_modified: Optional[datetime] = None

    def get_effective_config(self) -> Dict[str, Any]:
        """Get configuration with parameter overrides applied."""
        base_config = asdict(self)

        if self.parameter_overrides:
            # Deep merge overrides
            for key_path, value in self.parameter_overrides.items():
                self._apply_override(base_config, key_path, value)

        return base_config

    def _apply_override(self, config: Dict[str, Any], key_path: str, value: Any):
        """Apply parameter override using dot notation."""
        keys = key_path.split(".")
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value


class JSONStrategyLoader:
    """
    Load and manage JSON strategy configurations.

    Handles both Strategy Tab (testing with overrides) and
    Trading Tab (live execution) use cases.
    """

    def __init__(self, strategies_dir: str = None):
        if strategies_dir is None:
            # Find the correct path relative to project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent  # Go up to project root
            strategies_dir = (
                project_root / "backend" / "config" / "strategies" / "rules"
            )
        self.strategies_dir = Path(strategies_dir)
        self._strategy_cache: Dict[str, JSONStrategyConfig] = {}
        self._file_timestamps: Dict[str, datetime] = {}
        self._validation_cache: Dict[str, StrategyValidationResult] = {}

        # Required fields for strategy validation
        self.required_fields = {
            "strategy_name",
            "strategy_type",
            "module",
            "position_parameters",
            "entry_signals",
            "scoring",
        }

        logger.info(
            f"JSONStrategyLoader initialized with directory: {self.strategies_dir}"
        )

    def load_all_strategies(
        self, include_inactive: bool = False
    ) -> List[JSONStrategyConfig]:
        """
        Load all JSON strategy files from the rules directory.

        Args:
            include_inactive: Whether to include inactive strategies

        Returns:
            List of JSONStrategyConfig objects
        """
        strategies = []

        if not self.strategies_dir.exists():
            logger.error(f"Strategies directory does not exist: {self.strategies_dir}")
            return strategies

        json_files = list(self.strategies_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON strategy files")

        for json_file in json_files:
            try:
                strategy_config = self._load_strategy_file(json_file)
                if strategy_config:
                    if include_inactive or strategy_config.is_active:
                        strategies.append(strategy_config)
                        logger.debug(f"Loaded strategy: {strategy_config.strategy_id}")
            except Exception as e:
                logger.error(f"Failed to load strategy {json_file.name}: {e}")

        logger.info(f"Successfully loaded {len(strategies)} strategies")
        return strategies

    def load_strategy(
        self, strategy_id: str, use_cache: bool = True
    ) -> Optional[JSONStrategyConfig]:
        """
        Load specific strategy by ID.

        Args:
            strategy_id: Strategy identifier (filename without .json)
            use_cache: Whether to use cached version if available

        Returns:
            JSONStrategyConfig or None if not found
        """
        json_file = self.strategies_dir / f"{strategy_id}.json"

        if not json_file.exists():
            logger.warning(f"Strategy file not found: {json_file}")
            return None

        # Check cache and file timestamp
        if use_cache and strategy_id in self._strategy_cache:
            file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            cached_mtime = self._file_timestamps.get(strategy_id)

            if cached_mtime and file_mtime <= cached_mtime:
                logger.debug(f"Using cached strategy: {strategy_id}")
                return self._strategy_cache[strategy_id]

        # Load from file
        strategy_config = self._load_strategy_file(json_file)

        if strategy_config:
            # Update cache
            self._strategy_cache[strategy_id] = strategy_config
            self._file_timestamps[strategy_id] = datetime.fromtimestamp(
                json_file.stat().st_mtime
            )

        return strategy_config

    def _load_strategy_file(self, json_file: Path) -> Optional[JSONStrategyConfig]:
        """Load and parse a single JSON strategy file."""
        try:
            with open(json_file, "r") as f:
                raw_config = json.load(f)

            strategy_id = json_file.stem

            # Validate configuration
            validation_result = self._validate_strategy_config(strategy_id, raw_config)
            self._validation_cache[strategy_id] = validation_result

            if not validation_result.is_valid:
                logger.error(
                    f"Invalid strategy config {strategy_id}: {validation_result.errors}"
                )
                return None

            # Create structured config
            strategy_config = JSONStrategyConfig(
                strategy_id=strategy_id,
                strategy_name=raw_config.get("strategy_name", strategy_id),
                strategy_type=raw_config.get("strategy_type", "UNKNOWN"),
                description=raw_config.get("description", ""),
                module=raw_config.get("module", f"strategies.{strategy_id.lower()}"),
                # Required sections
                position_parameters=raw_config.get("position_parameters", {}),
                entry_signals=raw_config.get("entry_signals", {}),
                exit_rules=raw_config.get("exit_rules", {}),
                scoring=raw_config.get("scoring", {}),
                risk_management=raw_config.get("risk_management", {}),
                # Optional sections
                universe=raw_config.get("universe"),
                timing=raw_config.get("timing"),
                strike_selection=raw_config.get("strike_selection"),
                educational_content=raw_config.get("educational_content"),
                # Runtime state
                parameter_overrides=None,
                is_active=True,
                last_modified=datetime.now(),
            )

            return strategy_config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
            return None

    def _validate_strategy_config(
        self, strategy_id: str, config: Dict[str, Any]
    ) -> StrategyValidationResult:
        """Validate strategy configuration against requirements."""
        errors = []
        warnings = []

        # Check required fields
        for field in self.required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate strategy_type
        valid_types = {
            "THETA_HARVESTING",
            "RSI_COUPON",
            "IRON_CONDOR",
            "PUT_SPREAD",
            "COVERED_CALL",
            "CREDIT_SPREAD",
            "VERTICAL_SPREAD",
            "STRADDLE",
            "STRANGLE",
            "BUTTERFLY",
            "CALENDAR_SPREAD",
            "COLLAR",
            "PROTECTIVE_PUT",
            "NAKED_OPTION",
        }

        strategy_type = config.get("strategy_type", "").upper()
        if strategy_type and strategy_type not in valid_types:
            warnings.append(f"Unknown strategy_type: {strategy_type}")

        # Validate position_parameters
        position_params = config.get("position_parameters", {})
        if "max_opportunities" in position_params:
            max_opps = position_params["max_opportunities"]
            if not isinstance(max_opps, int) or max_opps < 1:
                errors.append("max_opportunities must be a positive integer")

        # Validate scoring section
        scoring = config.get("scoring", {})
        if "score_floor" in scoring and "score_ceiling" in scoring:
            floor = scoring["score_floor"]
            ceiling = scoring["score_ceiling"]
            if floor >= ceiling:
                errors.append("score_floor must be less than score_ceiling")

        # Validate exit_rules structure
        exit_rules = config.get("exit_rules", {})
        for rule_type in ["profit_targets", "stop_loss_rules", "time_exits"]:
            if rule_type in exit_rules:
                rules = exit_rules[rule_type]
                if not isinstance(rules, list):
                    errors.append(f"{rule_type} must be a list")
                else:
                    for i, rule in enumerate(rules):
                        if not isinstance(rule, dict):
                            errors.append(f"{rule_type}[{i}] must be an object")
                        elif "action" not in rule:
                            errors.append(
                                f"{rule_type}[{i}] missing required 'action' field"
                            )

        is_valid = len(errors) == 0

        return StrategyValidationResult(
            is_valid=is_valid, strategy_id=strategy_id, errors=errors, warnings=warnings
        )

    def apply_parameter_overrides(
        self, strategy_id: str, overrides: Dict[str, Any]
    ) -> bool:
        """
        Apply parameter overrides for Strategy Tab testing.

        Args:
            strategy_id: Strategy to modify
            overrides: Parameter overrides using dot notation

        Returns:
            True if successful
        """
        if strategy_id not in self._strategy_cache:
            # Load strategy first
            strategy_config = self.load_strategy(strategy_id)
            if not strategy_config:
                return False

        strategy_config = self._strategy_cache[strategy_id]

        if strategy_config.parameter_overrides is None:
            strategy_config.parameter_overrides = {}

        # Merge new overrides
        strategy_config.parameter_overrides.update(overrides)
        strategy_config.last_modified = datetime.now()

        logger.info(f"Applied parameter overrides to {strategy_id}: {overrides}")
        return True

    def clear_parameter_overrides(self, strategy_id: str) -> bool:
        """Clear all parameter overrides for a strategy."""
        if strategy_id in self._strategy_cache:
            self._strategy_cache[strategy_id].parameter_overrides = None
            self._strategy_cache[strategy_id].last_modified = datetime.now()
            logger.info(f"Cleared parameter overrides for {strategy_id}")
            return True
        return False

    def get_strategy_list(self) -> List[Dict[str, Any]]:
        """Get list of available strategies with metadata."""
        strategies_info = []

        for strategy_config in self.load_all_strategies():
            info = {
                "id": strategy_config.strategy_id,
                "name": strategy_config.strategy_name,
                "type": strategy_config.strategy_type,
                "description": strategy_config.description,
                "is_active": strategy_config.is_active,
                "has_overrides": strategy_config.parameter_overrides is not None,
                "last_modified": (
                    strategy_config.last_modified.isoformat()
                    if strategy_config.last_modified
                    else None
                ),
            }

            # Add validation status
            if strategy_config.strategy_id in self._validation_cache:
                validation = self._validation_cache[strategy_config.strategy_id]
                info["is_valid"] = validation.is_valid
                info["validation_errors"] = validation.errors
                info["validation_warnings"] = validation.warnings

            strategies_info.append(info)

        # Sort by strategy name
        strategies_info.sort(key=lambda x: x["name"])

        return strategies_info

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "cached_strategies": len(self._strategy_cache),
            "strategy_ids": list(self._strategy_cache.keys()),
            "validation_cache_size": len(self._validation_cache),
            "strategies_with_overrides": len(
                [
                    s
                    for s in self._strategy_cache.values()
                    if s.parameter_overrides is not None
                ]
            ),
        }
