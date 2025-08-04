"""Strategy registry for managing trading strategy plugins."""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type

from core.engines.engine_registry import EngineRegistry
from core.orchestrator.plugin_registry import PluginRegistry
from core.strategies.json_strategy_loader import JSONStrategyConfig, JSONStrategyLoader
from plugins.trading.base_strategy import (
    BaseStrategyPlugin,
    StrategyConfig,
    StrategyOpportunity,
)
from plugins.trading.json_strategy_plugin import JSONStrategyPlugin

logger = logging.getLogger(__name__)


@dataclass
class StrategyRegistration:
    """Registration information for a strategy plugin."""

    strategy_id: str
    strategy_class: Type[BaseStrategyPlugin]
    config: StrategyConfig
    enabled: bool = True
    registered_at: datetime = None
    last_scan: Optional[datetime] = None
    total_scans: int = 0
    total_opportunities: int = 0

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = datetime.utcnow()


class StrategyRegistry:
    """Registry for managing trading strategy plugins and their lifecycle."""

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        engine_registry: Optional[EngineRegistry] = None,
    ):
        self.plugin_registry = plugin_registry
        self.engine_registry = engine_registry
        self._strategies: Dict[str, StrategyRegistration] = {}
        self._strategy_instances: Dict[str, BaseStrategyPlugin] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._json_strategy_loader: Optional[JSONStrategyLoader] = None
        self._logger = logging.getLogger(__name__)

    def set_engine_registry(self, engine_registry: EngineRegistry):
        """Set the engine registry for JSON strategies."""
        self.engine_registry = engine_registry

    def register_strategy_class(
        self, strategy_class: Type[BaseStrategyPlugin], config: StrategyConfig
    ):
        """Register a strategy class with configuration."""
        strategy_id = config.strategy_id

        if strategy_id in self._strategies:
            self._logger.warning(
                f"Strategy {strategy_id} already registered, updating..."
            )

        registration = StrategyRegistration(
            strategy_id=strategy_id, strategy_class=strategy_class, config=config
        )

        self._strategies[strategy_id] = registration

        # Update category mapping
        category = config.category
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(strategy_id)

        self._logger.info(f"Registered strategy: {strategy_id} in category: {category}")

    def initialize_json_strategy_loader(self, strategies_dir: str = None):
        """Initialize the JSON strategy loader with environment-aware directory."""
        if strategies_dir is None:
            # Get environment from settings or environment variable
            from pathlib import Path

            from config.settings import get_settings

            settings = get_settings()
            raw_environment = os.getenv(
                "TRADING_ENVIRONMENT", settings.trading.environment
            )
            environment = raw_environment

            self._logger.info(
                f"Raw environment from settings: {settings.trading.environment}"
            )
            self._logger.info(
                f"TRADING_ENVIRONMENT env var: {os.getenv('TRADING_ENVIRONMENT', 'NOT SET')}"
            )
            self._logger.info(f"Final environment to use: {environment}")
            # Trigger reload

            # Get project root (go up from this file to project root)
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent

            # Try environment-specific directory first
            env_strategies_dir = (
                project_root / "backend" / "config" / "strategies" / environment
            )

            self._logger.info(f"Checking environment directory: {env_strategies_dir}")
            self._logger.info(
                f"Environment directory exists: {env_strategies_dir.exists()}"
            )

            # Check if environment directory exists and has JSON files
            if env_strategies_dir.exists():
                json_files = list(env_strategies_dir.glob("*.json"))
                self._logger.info(
                    f"JSON files found in environment directory: {len(json_files)}"
                )
                if json_files:
                    strategies_dir = str(env_strategies_dir)
                    self._logger.info(
                        f"Using environment-specific strategies directory: {strategies_dir} ({len(json_files)} files)"
                    )
                else:
                    self._logger.warning(
                        f"Environment directory {env_strategies_dir} exists but is empty"
                    )
            else:
                self._logger.warning(
                    f"Environment directory {env_strategies_dir} does not exist"
                )

            # Fallback to rules directory if environment directory is empty or doesn't exist
            if strategies_dir is None:
                rules_dir = project_root / "backend" / "config" / "strategies" / "rules"
                if rules_dir.exists():
                    json_files = list(rules_dir.glob("*.json"))
                    if json_files:
                        strategies_dir = str(rules_dir)
                        self._logger.info(
                            f"Falling back to rules directory: {strategies_dir} ({len(json_files)} files)"
                        )
                    else:
                        self._logger.error(
                            f"Rules directory {rules_dir} exists but is empty"
                        )

            # Final fallback - let JSONStrategyLoader use its default
            if strategies_dir is None:
                self._logger.warning(
                    "No strategy directories with JSON files found, using JSONStrategyLoader default"
                )
        else:
            # Extract environment from provided path if possible
            environment = (
                strategies_dir.split("/")[-1] if "/" in strategies_dir else "custom"
            )

        self._json_strategy_loader = JSONStrategyLoader(strategies_dir)
        actual_dir = self._json_strategy_loader.strategies_dir
        self._logger.info(
            f"Initialized JSON strategy loader with directory: {actual_dir}"
        )

    def register_json_strategies(self) -> int:
        """Register all JSON strategies from the rules directory."""
        if not self._json_strategy_loader:
            self.initialize_json_strategy_loader()

        if not self.engine_registry:
            self._logger.error(
                "Engine registry not available - cannot register JSON strategies"
            )
            return 0

        json_strategies = self._json_strategy_loader.load_all_strategies(
            include_inactive=False
        )
        registered_count = 0

        for json_config in json_strategies:
            try:
                # Convert JSON config to StrategyConfig for compatibility
                strategy_config = StrategyConfig(
                    strategy_id=json_config.strategy_id,
                    name=json_config.strategy_name,
                    category=json_config.strategy_type.lower()
                    .replace("_", " ")
                    .title(),
                    min_dte=json_config.position_parameters.get("min_dte", 7),
                    max_dte=json_config.position_parameters.get("max_dte", 45),
                    min_probability=json_config.position_parameters.get(
                        "min_probability", 0.65
                    ),
                    max_opportunities=json_config.position_parameters.get(
                        "max_opportunities", 10
                    ),
                    symbols=(
                        json_config.universe.get(
                            "preferred_symbols", ["SPY", "QQQ", "IWM"]
                        )
                        if json_config.universe
                        else ["SPY", "QQQ", "IWM"]
                    ),
                    min_liquidity_score=json_config.position_parameters.get(
                        "min_liquidity_score", 7.0
                    ),
                    max_risk_per_trade=json_config.risk_management.get(
                        "max_loss_per_trade", 500.0
                    ),
                )

                # Create registration for JSON strategy
                registration = StrategyRegistration(
                    strategy_id=json_config.strategy_id,
                    strategy_class=JSONStrategyPlugin,
                    config=strategy_config,
                    enabled=json_config.is_active,
                )

                self._strategies[json_config.strategy_id] = registration

                # Update category mapping
                category = strategy_config.category
                if category not in self._categories:
                    self._categories[category] = set()
                self._categories[category].add(json_config.strategy_id)

                registered_count += 1
                self._logger.info(
                    f"Registered JSON strategy: {json_config.strategy_id} ({json_config.strategy_type})"
                )

            except Exception as e:
                self._logger.error(
                    f"Failed to register JSON strategy {json_config.strategy_id}: {e}"
                )

        self._logger.info(f"Registered {registered_count} JSON strategies")
        return registered_count

    async def create_strategy_instance(
        self, strategy_id: str
    ) -> Optional[BaseStrategyPlugin]:
        """Create an instance of a registered strategy."""
        if strategy_id not in self._strategies:
            self._logger.error(f"Strategy {strategy_id} not registered")
            return None

        registration = self._strategies[strategy_id]

        try:
            # Create plugin config
            from core.orchestrator.base_plugin import PluginConfig

            plugin_config = PluginConfig(enabled=registration.enabled)

            # Check if this is a JSON strategy
            if registration.strategy_class == JSONStrategyPlugin:
                if not self._json_strategy_loader:
                    self._logger.error(
                        f"JSON strategy loader not initialized for {strategy_id}"
                    )
                    return None

                # Load JSON configuration
                json_config = self._json_strategy_loader.load_strategy(strategy_id)
                if not json_config:
                    self._logger.error(f"Failed to load JSON config for {strategy_id}")
                    return None

                # Create JSONStrategyPlugin with both configurations
                instance = registration.strategy_class(
                    config=plugin_config,
                    strategy_config=registration.config,
                    json_config=json_config,
                    engine_registry=self.engine_registry,
                )
            else:
                # Create regular strategy plugin
                instance = registration.strategy_class(
                    config=plugin_config, strategy_config=registration.config
                )

            # Initialize the strategy
            success = await instance._safe_initialize()
            if not success:
                self._logger.error(f"Failed to initialize strategy: {strategy_id}")
                return None

            self._strategy_instances[strategy_id] = instance
            self._logger.info(
                f"Created and initialized strategy instance: {strategy_id}"
            )

            return instance

        except Exception as e:
            self._logger.error(f"Failed to create strategy instance {strategy_id}: {e}")
            return None

    async def initialize_all_strategies(self) -> bool:
        """Initialize all registered strategies."""
        success_count = 0
        total_count = len(self._strategies)

        for strategy_id in self._strategies:
            registration = self._strategies[strategy_id]
            if registration.enabled:
                instance = await self.create_strategy_instance(strategy_id)
                if instance:
                    success_count += 1

        success_rate = success_count / total_count if total_count > 0 else 0
        self._logger.info(
            f"Initialized {success_count}/{total_count} strategies (success rate: {success_rate:.1%})"
        )

        return success_rate >= 0.8  # 80% success rate threshold

    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategyPlugin]:
        """Get a strategy instance by ID."""
        return self._strategy_instances.get(strategy_id)

    def get_strategies_by_category(self, category: str) -> List[BaseStrategyPlugin]:
        """Get all strategy instances in a category."""
        if category not in self._categories:
            return []

        instances = []
        for strategy_id in self._categories[category]:
            instance = self._strategy_instances.get(strategy_id)
            if instance:
                instances.append(instance)

        return instances

    def get_all_strategies(self) -> List[BaseStrategyPlugin]:
        """Get all strategy instances."""
        return list(self._strategy_instances.values())

    def get_all_registrations(self) -> Dict[str, StrategyRegistration]:
        """Get all strategy registrations."""
        return self._strategies.copy()

    def get_categories(self) -> List[str]:
        """Get all strategy categories."""
        return list(self._categories.keys())

    async def scan_all_strategies(
        self, universe: List[str], **kwargs
    ) -> Dict[str, List[StrategyOpportunity]]:
        """Scan for opportunities across all enabled strategies."""
        results = {}
        tasks = []

        for strategy_id, instance in self._strategy_instances.items():
            registration = self._strategies[strategy_id]
            if registration.enabled:
                task = self._scan_strategy_safe(
                    strategy_id, instance, universe, **kwargs
                )
                tasks.append(task)

        # Execute all scans concurrently
        scan_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        strategy_ids = [
            sid
            for sid, inst in self._strategy_instances.items()
            if self._strategies[sid].enabled
        ]
        for i, result in enumerate(scan_results):
            strategy_id = strategy_ids[i]

            if isinstance(result, Exception):
                self._logger.error(f"Strategy {strategy_id} scan failed: {result}")
                results[strategy_id] = []
            else:
                results[strategy_id] = result

                # Update registration stats
                registration = self._strategies[strategy_id]
                registration.last_scan = datetime.utcnow()
                registration.total_scans += 1
                registration.total_opportunities += len(result)

        return results

    async def _scan_strategy_safe(
        self,
        strategy_id: str,
        instance: BaseStrategyPlugin,
        universe: List[str],
        **kwargs,
    ) -> List[StrategyOpportunity]:
        """Safely scan a strategy with error handling."""
        try:
            opportunities = await instance.scan_opportunities(universe, **kwargs)
            self._logger.debug(
                f"Strategy {strategy_id} found {len(opportunities)} opportunities"
            )
            return opportunities
        except Exception as e:
            self._logger.error(f"Strategy {strategy_id} scan error: {e}")
            return []

    async def enable_strategy(self, strategy_id: str) -> bool:
        """Enable a strategy."""
        if strategy_id not in self._strategies:
            return False

        registration = self._strategies[strategy_id]
        registration.enabled = True

        # Create instance if not exists
        if strategy_id not in self._strategy_instances:
            instance = await self.create_strategy_instance(strategy_id)
            return instance is not None

        return True

    async def disable_strategy(self, strategy_id: str) -> bool:
        """Disable a strategy."""
        if strategy_id not in self._strategies:
            return False

        registration = self._strategies[strategy_id]
        registration.enabled = False

        # Clean up instance
        if strategy_id in self._strategy_instances:
            instance = self._strategy_instances[strategy_id]
            await instance._safe_cleanup()
            del self._strategy_instances[strategy_id]

        return True

    def get_strategy_status(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive status for a strategy."""
        if strategy_id not in self._strategies:
            return None

        registration = self._strategies[strategy_id]
        instance = self._strategy_instances.get(strategy_id)

        status = {
            "strategy_id": strategy_id,
            "enabled": registration.enabled,
            "registered_at": registration.registered_at.isoformat(),
            "last_scan": (
                registration.last_scan.isoformat() if registration.last_scan else None
            ),
            "total_scans": registration.total_scans,
            "total_opportunities": registration.total_opportunities,
            "category": registration.config.category,
            "config": {
                "name": registration.config.name,
                "min_dte": registration.config.min_dte,
                "max_dte": registration.config.max_dte,
                "min_probability": registration.config.min_probability,
                "max_opportunities": registration.config.max_opportunities,
            },
        }

        if instance:
            plugin_status = instance.get_status()
            status.update(
                {
                    "plugin_status": plugin_status["status"],
                    "health_check_failures": plugin_status["health_check_failures"],
                    "last_health_check": plugin_status["last_health_check"],
                    "performance_stats": instance.get_performance_stats(),
                }
            )
        else:
            status.update(
                {
                    "plugin_status": "not_instantiated",
                    "health_check_failures": 0,
                    "last_health_check": None,
                    "performance_stats": {},
                }
            )

        return status

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall strategy system status."""
        total_strategies = len(self._strategies)
        enabled_strategies = sum(1 for reg in self._strategies.values() if reg.enabled)
        active_instances = len(self._strategy_instances)

        categories_stats = {}
        for category, strategy_ids in self._categories.items():
            enabled_in_category = sum(
                1 for sid in strategy_ids if self._strategies[sid].enabled
            )
            categories_stats[category] = {
                "total": len(strategy_ids),
                "enabled": enabled_in_category,
                "active_instances": sum(
                    1 for sid in strategy_ids if sid in self._strategy_instances
                ),
            }

        return {
            "total_strategies": total_strategies,
            "enabled_strategies": enabled_strategies,
            "active_instances": active_instances,
            "categories": categories_stats,
            "strategy_categories": list(self._categories.keys()),
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def cleanup_all(self) -> bool:
        """Cleanup all strategy instances."""
        cleanup_tasks = []

        for strategy_id, instance in self._strategy_instances.items():
            cleanup_tasks.append(instance._safe_cleanup())

        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            self._logger.info(
                f"Cleaned up {success_count}/{len(cleanup_tasks)} strategy instances"
            )

        self._strategy_instances.clear()
        return True


# Global strategy registry instance
_strategy_registry: Optional[StrategyRegistry] = None


def initialize_strategy_registry(plugin_registry: PluginRegistry) -> StrategyRegistry:
    """Initialize the global strategy registry."""
    global _strategy_registry
    _strategy_registry = StrategyRegistry(plugin_registry)
    return _strategy_registry


def get_strategy_registry() -> Optional[StrategyRegistry]:
    """Get the global strategy registry instance."""
    return _strategy_registry
