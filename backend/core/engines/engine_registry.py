"""
Engine Registry
===============
Registry for data provider engines with runtime switching capability.
Supports the engines pattern for clean strategy integration.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from core.interfaces.data_provider_interface import (
    DataProviderAdapter,
    DataProviderType,
    IDataProvider,
)
from core.orchestrator.base_plugin import PluginType
from core.orchestrator.plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)


class EngineType(Enum):
    """Types of engines supported by the registry."""

    DATA_PROVIDER = "data_provider"
    EXECUTION = "execution"
    RISK_MANAGEMENT = "risk"
    PORTFOLIO = "portfolio"


class EngineRegistry:
    """
    Registry for strategy engines with runtime switching capability.

    This registry provides a centralized way to manage and access different
    engines that strategies need, with support for configuration-driven
    provider switching.
    """

    def __init__(self, plugin_registry: Optional[PluginRegistry] = None):
        self.plugin_registry = plugin_registry
        self._engines: Dict[str, Dict[str, Any]] = {
            EngineType.DATA_PROVIDER.value: {},
            EngineType.EXECUTION.value: {},
            EngineType.RISK_MANAGEMENT.value: {},
            EngineType.PORTFOLIO.value: {},
        }
        self._default_providers: Dict[str, str] = {}
        self._fallback_providers: Dict[str, List[str]] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the engine registry with configuration.

        Args:
            config: Configuration dict with engine settings
        """
        if self._initialized:
            logger.warning("EngineRegistry already initialized")
            return

        config = config or {}

        # Initialize data providers from plugin registry
        await self._initialize_data_providers(config.get("data", {}))

        # Initialize other engines
        await self._initialize_other_engines(config.get("engines", {}))

        # Set default and fallback providers
        self._configure_defaults(config)

        self._initialized = True
        logger.info("✅ EngineRegistry initialized successfully")

    async def _initialize_data_providers(self, data_config: Dict[str, Any]):
        """Initialize data provider engines from plugin registry."""
        if not self.plugin_registry:
            logger.warning(
                "No plugin registry provided - data providers will not be available"
            )
            return

        # Get available data provider plugins
        available_plugins = self.plugin_registry.get_plugins_by_type(
            PluginType.DATA_PROVIDER
        )

        for plugin_instance in available_plugins:
            try:
                # Get plugin name from metadata
                plugin_name = plugin_instance.metadata.name

                # Wrap existing plugin with adapter to implement unified interface
                adapter = DataProviderAdapter(plugin_instance)

                # Map plugin names to provider types
                provider_type = self._map_plugin_to_provider_type(plugin_name)
                if provider_type:
                    self._engines[EngineType.DATA_PROVIDER.value][
                        provider_type.value
                    ] = adapter
                    logger.info(
                        f"✅ Registered data provider: {provider_type.value} ({plugin_name})"
                    )
                else:
                    logger.warning(f"Unknown plugin type for {plugin_name}")

            except Exception as e:
                logger.error(f"❌ Failed to register data provider {plugin_name}: {e}")

    def _map_plugin_to_provider_type(
        self, plugin_name: str
    ) -> Optional[DataProviderType]:
        """Map plugin names to DataProviderType enum values."""
        mapping = {
            "yfinance_provider": DataProviderType.YFINANCE,
            "alpaca_provider": DataProviderType.ALPACA,
            "mock_provider": DataProviderType.MOCK,
        }
        return mapping.get(plugin_name.lower())

    async def _initialize_other_engines(self, engines_config: Dict[str, Any]):
        """Initialize non-data-provider engines."""
        # Placeholder for future engines (execution, risk management, etc.)
        # For now, we'll focus on data providers

        # Execution engine placeholder
        self._engines[EngineType.EXECUTION.value]["sandbox"] = SandboxExecutionEngine()

        # Risk management engine placeholder
        self._engines[EngineType.RISK_MANAGEMENT.value][
            "standard"
        ] = StandardRiskEngine()

        logger.info("✅ Other engines initialized")

    def _configure_defaults(self, config: Dict[str, Any]):
        """Configure default and fallback providers."""
        data_config = config.get("data", {})

        # Set default data provider
        default_provider = data_config.get("primary_provider", "yfinance")
        if default_provider in self._engines[EngineType.DATA_PROVIDER.value]:
            self._default_providers[EngineType.DATA_PROVIDER.value] = default_provider
        else:
            # Fallback to first available provider
            available = list(self._engines[EngineType.DATA_PROVIDER.value].keys())
            if available:
                self._default_providers[EngineType.DATA_PROVIDER.value] = available[0]
                logger.warning(
                    f"Default provider {default_provider} not available, using {available[0]}"
                )

        # Set fallback providers
        fallback_providers = data_config.get("fallback_providers", ["yfinance"])
        self._fallback_providers[EngineType.DATA_PROVIDER.value] = [
            p
            for p in fallback_providers
            if p in self._engines[EngineType.DATA_PROVIDER.value]
        ]

        logger.info(
            f"Default data provider: {self._default_providers.get(EngineType.DATA_PROVIDER.value)}"
        )
        logger.info(
            f"Fallback providers: {self._fallback_providers.get(EngineType.DATA_PROVIDER.value, [])}"
        )

    def get_data_provider(
        self, provider_type: Optional[DataProviderType] = None
    ) -> Optional[IDataProvider]:
        """
        Get data provider engine with fallback support.

        Args:
            provider_type: Specific provider to get, or None for default

        Returns:
            IDataProvider instance or None if not available
        """
        if not self._initialized:
            logger.error("EngineRegistry not initialized")
            return None

        provider_key = provider_type.value if provider_type else None
        engines = self._engines[EngineType.DATA_PROVIDER.value]

        # Try specific provider first
        if provider_key and provider_key in engines:
            return engines[provider_key]

        # Try default provider
        default_key = self._default_providers.get(EngineType.DATA_PROVIDER.value)
        if default_key and default_key in engines:
            return engines[default_key]

        # Try fallback providers
        fallbacks = self._fallback_providers.get(EngineType.DATA_PROVIDER.value, [])
        for fallback_key in fallbacks:
            if fallback_key in engines:
                logger.warning(f"Using fallback data provider: {fallback_key}")
                return engines[fallback_key]

        # Last resort - any available provider
        if engines:
            available_key = list(engines.keys())[0]
            logger.warning(f"Using last resort data provider: {available_key}")
            return engines[available_key]

        logger.error("No data providers available")
        return None

    def get_engine(
        self, engine_type: EngineType, engine_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get any type of engine by type and name.

        Args:
            engine_type: Type of engine (DATA_PROVIDER, EXECUTION, etc.)
            engine_name: Specific engine name, or None for default

        Returns:
            Engine instance or None if not available
        """
        if not self._initialized:
            logger.error("EngineRegistry not initialized")
            return None

        engines = self._engines.get(engine_type.value, {})

        if engine_name and engine_name in engines:
            return engines[engine_name]

        # Return first available engine if no specific name requested
        if not engine_name and engines:
            return list(engines.values())[0]

        return None

    def get_engines_dict(
        self, provider_type: Optional[DataProviderType] = None
    ) -> Dict[str, Any]:
        """
        Get engines dictionary for strategy use.

        Args:
            provider_type: Data provider to use, or None for default

        Returns:
            Dict of engines keyed by engine type
        """
        if not self._initialized:
            logger.error("EngineRegistry not initialized")
            return {}

        return {
            "data_provider": self.get_data_provider(provider_type),
            "execution": self.get_engine(EngineType.EXECUTION, "sandbox"),
            "risk": self.get_engine(EngineType.RISK_MANAGEMENT, "standard"),
            "portfolio": self.get_engine(EngineType.PORTFOLIO),
        }

    def list_available_providers(self) -> Dict[str, List[str]]:
        """List all available providers by engine type."""
        return {
            engine_type: list(engines.keys())
            for engine_type, engines in self._engines.items()
            if engines
        }

    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about registered providers."""
        stats = {
            "total_engines": sum(len(engines) for engines in self._engines.values()),
            "data_providers": len(self._engines[EngineType.DATA_PROVIDER.value]),
            "available_providers": self.list_available_providers(),
            "default_data_provider": self._default_providers.get(
                EngineType.DATA_PROVIDER.value
            ),
            "fallback_providers": self._fallback_providers.get(
                EngineType.DATA_PROVIDER.value, []
            ),
        }

        # Add cache stats from data providers
        data_providers = self._engines[EngineType.DATA_PROVIDER.value]
        cache_stats = {}
        for provider_name, provider in data_providers.items():
            if hasattr(provider, "get_cache_stats"):
                try:
                    cache_stats[provider_name] = provider.get_cache_stats()
                except Exception as e:
                    logger.warning(
                        f"Failed to get cache stats from {provider_name}: {e}"
                    )

        if cache_stats:
            stats["cache_stats"] = cache_stats

        return stats


# Placeholder engine classes for future implementation
class SandboxExecutionEngine:
    """Placeholder execution engine for sandbox/paper trading."""

    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place a sandbox order (no real execution)."""
        logger.info(f"📝 Sandbox order placed: {order}")
        return {
            "order_id": f"sandbox_{order.get('symbol', 'unknown')}_{order.get('quantity', 0)}",
            "status": "filled",
            "fill_price": order.get("price", 0.0),
            "timestamp": logger.info("Order timestamp"),
        }

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions (empty for sandbox)."""
        return []


class StandardRiskEngine:
    """Placeholder risk management engine."""

    def validate_trade(self, trade: Dict[str, Any]) -> bool:
        """Validate trade against risk parameters."""
        # Basic validation - can be enhanced later
        return True

    def calculate_position_size(
        self, opportunity: Dict[str, Any], account_size: float
    ) -> int:
        """Calculate appropriate position size."""
        # Simple position sizing - can be enhanced later
        return 1
