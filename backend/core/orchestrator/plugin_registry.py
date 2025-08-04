"""Plugin registry for managing all plugins in the system."""

import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, Type

from .base_plugin import BasePlugin, PluginConfig, PluginStatus, PluginType
from .event_bus import EventBus, EventType, PluginEvent

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when plugin dependencies cannot be resolved."""

    pass


class PluginRegistry:
    """Central registry for managing all plugins."""

    def __init__(self, event_bus: EventBus = None):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._plugins_by_type: Dict[PluginType, List[BasePlugin]] = defaultdict(list)
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._initialization_order: List[str] = []
        self._event_bus = event_bus or EventBus()
        self._lock = asyncio.Lock()

    def register_plugin_class(self, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class for later instantiation."""
        # Create temporary instance to get metadata
        temp_instance = plugin_class()
        plugin_name = temp_instance.metadata.name

        self._plugin_classes[plugin_name] = plugin_class
        logger.info(f"Registered plugin class: {plugin_name}")

    async def create_plugin(
        self, plugin_name: str, config: PluginConfig = None
    ) -> BasePlugin:
        """Create and register a plugin instance."""
        async with self._lock:
            if plugin_name in self._plugins:
                raise ValueError(f"Plugin already exists: {plugin_name}")

            if plugin_name not in self._plugin_classes:
                raise ValueError(f"Plugin class not registered: {plugin_name}")

            plugin_class = self._plugin_classes[plugin_name]
            plugin = plugin_class(config)

            # Validate configuration
            if not await plugin.validate_config(config.settings if config else {}):
                raise ValueError(f"Invalid configuration for plugin: {plugin_name}")

            # Build dependency graph
            self._build_dependency_graph(plugin)

            # Register plugin
            self._plugins[plugin_name] = plugin
            self._plugins_by_type[plugin.metadata.plugin_type].append(plugin)

            logger.info(f"Created plugin: {plugin_name}")
            await self._event_bus.emit(
                PluginEvent(
                    event_type=EventType.PLUGIN_REGISTERED,
                    plugin_name=plugin_name,
                    data={"plugin_type": plugin.metadata.plugin_type.value},
                )
            )

            return plugin

    def _build_dependency_graph(self, plugin: BasePlugin) -> None:
        """Build dependency graph for plugin ordering."""
        plugin_name = plugin.metadata.name
        dependencies = plugin.metadata.dependencies or []

        for dep in dependencies:
            self._dependency_graph[plugin_name].add(dep)
            self._reverse_dependencies[dep].add(plugin_name)

    def _resolve_initialization_order(self) -> List[str]:
        """Resolve plugin initialization order using topological sort."""
        # Kahn's algorithm for topological sorting
        in_degree = defaultdict(int)

        # Calculate in-degrees
        for plugin_name in self._plugins:
            for dependency in self._dependency_graph[plugin_name]:
                in_degree[plugin_name] += 1

        # Initialize queue with plugins that have no dependencies
        queue = [name for name in self._plugins if in_degree[name] == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            # Reduce in-degree for dependents
            for dependent in self._reverse_dependencies[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(order) != len(self._plugins):
            remaining = set(self._plugins.keys()) - set(order)
            raise DependencyError(
                f"Circular dependency detected among plugins: {remaining}"
            )

        return order

    async def initialize_all(self) -> bool:
        """Initialize all plugins in dependency order."""
        async with self._lock:
            try:
                self._initialization_order = self._resolve_initialization_order()
                logger.info(
                    f"Plugin initialization order: {self._initialization_order}"
                )

                success_count = 0
                for plugin_name in self._initialization_order:
                    plugin = self._plugins[plugin_name]

                    if not plugin.config.enabled:
                        logger.info(f"Skipping disabled plugin: {plugin_name}")
                        continue

                    try:
                        success = await plugin._safe_initialize()
                        if success:
                            success_count += 1
                            await self._event_bus.emit(
                                PluginEvent(
                                    event_type=EventType.PLUGIN_INITIALIZED,
                                    plugin_name=plugin_name,
                                )
                            )
                        else:
                            await self._event_bus.emit(
                                PluginEvent(
                                    event_type=EventType.PLUGIN_ERROR,
                                    plugin_name=plugin_name,
                                    data={"error": "Initialization failed"},
                                )
                            )
                    except Exception as e:
                        logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
                        await self._event_bus.emit(
                            PluginEvent(
                                event_type=EventType.PLUGIN_ERROR,
                                plugin_name=plugin_name,
                                data={"error": str(e)},
                            )
                        )

                total_enabled = sum(
                    1 for p in self._plugins.values() if p.config.enabled
                )
                logger.info(
                    f"Initialized {success_count}/{total_enabled} enabled plugins"
                )
                return success_count == total_enabled

            except Exception as e:
                logger.error(f"Plugin initialization failed: {e}")
                return False

    async def cleanup_all(self) -> bool:
        """Clean up all plugins in reverse dependency order."""
        async with self._lock:
            try:
                # Cleanup in reverse order
                cleanup_order = list(reversed(self._initialization_order))
                success_count = 0

                for plugin_name in cleanup_order:
                    if plugin_name not in self._plugins:
                        continue

                    plugin = self._plugins[plugin_name]
                    if plugin.status != PluginStatus.ACTIVE:
                        continue

                    try:
                        success = await plugin._safe_cleanup()
                        if success:
                            success_count += 1
                            await self._event_bus.emit(
                                PluginEvent(
                                    event_type=EventType.PLUGIN_CLEANUP,
                                    plugin_name=plugin_name,
                                )
                            )
                    except Exception as e:
                        logger.error(f"Failed to cleanup plugin {plugin_name}: {e}")

                logger.info(f"Cleaned up {success_count} plugins")
                return True

            except Exception as e:
                logger.error(f"Plugin cleanup failed: {e}")
                return False

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        return self._plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Get all plugins of a specific type."""
        return [
            p
            for p in self._plugins_by_type[plugin_type]
            if p.status == PluginStatus.ACTIVE and p.config.enabled
        ]

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    async def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all active plugins."""
        results = {}

        for plugin_name, plugin in self._plugins.items():
            if plugin.status == PluginStatus.ACTIVE:
                try:
                    is_healthy = await plugin.health_check()
                    results[plugin_name] = is_healthy

                    if not is_healthy:
                        plugin._health_check_failures += 1
                        await self._event_bus.emit(
                            PluginEvent(
                                event_type=EventType.PLUGIN_HEALTH_CHECK_FAILED,
                                plugin_name=plugin_name,
                                data={"failure_count": plugin._health_check_failures},
                            )
                        )
                    else:
                        plugin._health_check_failures = 0

                except Exception as e:
                    logger.error(f"Health check failed for {plugin_name}: {e}")
                    results[plugin_name] = False
                    plugin._health_check_failures += 1

        return results

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        total_plugins = len(self._plugins)
        active_plugins = sum(
            1 for p in self._plugins.values() if p.status == PluginStatus.ACTIVE
        )
        enabled_plugins = sum(1 for p in self._plugins.values() if p.config.enabled)

        plugin_status = {}
        for name, plugin in self._plugins.items():
            plugin_status[name] = plugin.get_status()

        return {
            "total_plugins": total_plugins,
            "active_plugins": active_plugins,
            "enabled_plugins": enabled_plugins,
            "initialization_order": self._initialization_order,
            "plugins": plugin_status,
        }

    @asynccontextmanager
    async def managed_lifecycle(self):
        """Context manager for plugin lifecycle management."""
        try:
            await self.initialize_all()
            yield self
        finally:
            await self.cleanup_all()
