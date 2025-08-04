"""Base plugin interface for all plugin types in the dynamic option pilot system."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin lifecycle status."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """Types of plugins in the system."""

    DATA_PROVIDER = "data_provider"
    ANALYSIS = "analysis"
    TRADING_STRATEGY = "trading_strategy"
    EXECUTION = "execution"
    RISK_MANAGEMENT = "risk_management"


@dataclass
class PluginMetadata:
    """Metadata for plugin registration and management."""

    name: str
    version: str
    plugin_type: PluginType
    description: str
    author: str
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}


@dataclass
class PluginConfig:
    """Configuration for plugin instances."""

    enabled: bool = True
    settings: Dict[str, Any] = None
    priority: int = 100  # Lower numbers = higher priority

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}


class BasePlugin(ABC):
    """Abstract base class for all plugins."""

    def __init__(self, config: PluginConfig = None):
        self.config = config or PluginConfig()
        self.status = PluginStatus.UNINITIALIZED
        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._health_check_failures = 0
        self._last_health_check = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up plugin resources. Return True if successful."""
        pass

    async def health_check(self) -> bool:
        """Check if plugin is healthy. Override for custom health checks."""
        self._last_health_check = datetime.utcnow()
        return self.status == PluginStatus.ACTIVE

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration against schema."""
        try:
            if not self.metadata.config_schema:
                return True

            # Basic validation - can be enhanced with jsonschema
            for required_field in self.metadata.config_schema.get("required", []):
                if required_field not in config:
                    self._logger.error(
                        f"Missing required config field: {required_field}"
                    )
                    return False

            return True
        except Exception as e:
            self._logger.error(f"Config validation error: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information."""
        return {
            "name": self.metadata.name,
            "status": self.status.value,
            "health_check_failures": self._health_check_failures,
            "last_health_check": (
                self._last_health_check.isoformat() if self._last_health_check else None
            ),
            "config": {
                "enabled": self.config.enabled,
                "priority": self.config.priority,
            },
        }

    async def _safe_initialize(self) -> bool:
        """Safely initialize plugin with error handling."""
        try:
            self.status = PluginStatus.INITIALIZING
            self._logger.info(f"Initializing plugin: {self.metadata.name}")

            result = await self.initialize()
            if result:
                self.status = PluginStatus.ACTIVE
                self._logger.info(
                    f"Plugin initialized successfully: {self.metadata.name}"
                )
            else:
                self.status = PluginStatus.ERROR
                self._logger.error(
                    f"Plugin initialization failed: {self.metadata.name}"
                )

            return result
        except Exception as e:
            self.status = PluginStatus.ERROR
            self._logger.error(
                f"Plugin initialization error: {self.metadata.name} - {e}"
            )
            return False

    async def _safe_cleanup(self) -> bool:
        """Safely cleanup plugin with error handling."""
        try:
            self._logger.info(f"Cleaning up plugin: {self.metadata.name}")
            result = await self.cleanup()
            if result:
                self.status = PluginStatus.DISABLED
                self._logger.info(
                    f"Plugin cleaned up successfully: {self.metadata.name}"
                )
            else:
                self._logger.error(f"Plugin cleanup failed: {self.metadata.name}")
            return result
        except Exception as e:
            self._logger.error(f"Plugin cleanup error: {self.metadata.name} - {e}")
            return False


class DataProviderPlugin(BasePlugin):
    """Base class for data provider plugins."""

    @abstractmethod
    async def get_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get market data for a symbol."""
        pass

    @abstractmethod
    async def get_options_chain(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get options chain for a symbol."""
        pass


class AnalysisPlugin(BasePlugin):
    """Base class for analysis plugins."""

    @abstractmethod
    async def analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform analysis on the provided data."""
        pass


class TradingStrategyPlugin(BasePlugin):
    """Base class for trading strategy plugins."""

    @abstractmethod
    async def scan_opportunities(
        self, universe: List[str], **kwargs
    ) -> List[Dict[str, Any]]:
        """Scan for trading opportunities."""
        pass

    @abstractmethod
    async def validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Validate a trading opportunity."""
        pass


class ExecutionPlugin(BasePlugin):
    """Base class for execution plugins."""

    @abstractmethod
    async def execute_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        pass


class RiskManagementPlugin(BasePlugin):
    """Base class for risk management plugins."""

    @abstractmethod
    async def assess_risk(
        self, portfolio: Dict[str, Any], trade: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk for a potential trade."""
        pass

    @abstractmethod
    async def check_limits(self, trade: Dict[str, Any]) -> bool:
        """Check if trade is within risk limits."""
        pass
