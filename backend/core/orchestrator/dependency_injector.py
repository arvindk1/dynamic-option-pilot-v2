"""Dependency injection container for plugin system."""

from typing import Dict, Any, TypeVar, Type, Optional, Callable, List
import inspect
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """Dependency injection container for plugins and services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        key = self._get_key(interface)
        self._singletons[key] = instance
        logger.debug(f"Registered singleton: {key}")
    
    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for creating instances."""
        key = self._get_key(interface)
        self._factories[key] = factory
        self._analyze_dependencies(factory)
        logger.debug(f"Registered factory: {key}")
    
    def register_service(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a service implementation."""
        key = self._get_key(interface)
        self._services[key] = implementation
        self._analyze_dependencies(implementation.__init__)
        logger.debug(f"Registered service: {key} -> {implementation.__name__}")
    
    def _get_key(self, interface: Type) -> str:
        """Get string key for interface type."""
        return f"{interface.__module__}.{interface.__name__}"
    
    def _analyze_dependencies(self, func: Callable) -> None:
        """Analyze function dependencies for dependency graph."""
        try:
            sig = inspect.signature(func)
            func_key = f"{func.__module__}.{func.__name__}"
            dependencies = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                if param.annotation != inspect.Parameter.empty:
                    dep_key = self._get_key(param.annotation)
                    dependencies.append(dep_key)
            
            self._dependency_graph[func_key] = dependencies
            
        except Exception as e:
            logger.warning(f"Could not analyze dependencies for {func}: {e}")
    
    async def resolve(self, interface: Type[T]) -> T:
        """Resolve an instance of the requested interface."""
        key = self._get_key(interface)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            factory = self._factories[key]
            dependencies = await self._resolve_dependencies(factory)
            
            if asyncio.iscoroutinefunction(factory):
                instance = await factory(**dependencies)
            else:
                instance = factory(**dependencies)
            
            return instance
        
        # Check services
        if key in self._services:
            service_class = self._services[key]
            dependencies = await self._resolve_dependencies(service_class.__init__)
            instance = service_class(**dependencies)
            return instance
        
        raise ValueError(f"No registration found for: {interface}")
    
    async def _resolve_dependencies(self, func: Callable) -> Dict[str, Any]:
        """Resolve all dependencies for a function."""
        dependencies = {}
        
        try:
            sig = inspect.signature(func)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    dependency = await self.resolve(param.annotation)
                    dependencies[param_name] = dependency
                elif param.default != inspect.Parameter.empty:
                    # Use default value if no annotation
                    dependencies[param_name] = param.default
                else:
                    logger.warning(f"Cannot resolve parameter {param_name} for {func}")
        
        except Exception as e:
            logger.error(f"Error resolving dependencies for {func}: {e}")
            raise
        
        return dependencies
    
    def create_injected(self, func: Callable) -> Callable:
        """Decorator to automatically inject dependencies into function calls."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Only inject dependencies not already provided
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            
            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments and param_name != 'self':
                    if param.annotation != inspect.Parameter.empty:
                        try:
                            dependency = await self.resolve(param.annotation)
                            kwargs[param_name] = dependency
                        except ValueError:
                            # Dependency not registered, skip if has default
                            if param.default == inspect.Parameter.empty:
                                logger.warning(f"Cannot inject {param_name} into {func.__name__}")
            
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    def list_registrations(self) -> Dict[str, str]:
        """List all registered services and their types."""
        registrations = {}
        
        for key in self._singletons:
            registrations[key] = "singleton"
        
        for key in self._factories:
            registrations[key] = "factory"
        
        for key in self._services:
            registrations[key] = "service"
        
        return registrations
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the dependency graph."""
        return self._dependency_graph.copy()
    
    def clear(self) -> None:
        """Clear all registrations."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._dependency_graph.clear()
        logger.info("Cleared all dependency registrations")


# Global container instance
container = DependencyContainer()


def inject(func: Callable) -> Callable:
    """Decorator to inject dependencies into a function."""
    return container.create_injected(func)


def register_singleton(interface: Type[T], instance: T) -> None:
    """Register a singleton instance globally."""
    container.register_singleton(interface, instance)


def register_factory(interface: Type[T], factory: Callable[..., T]) -> None:
    """Register a factory function globally."""
    container.register_factory(interface, factory)


def register_service(interface: Type[T], implementation: Type[T]) -> None:
    """Register a service implementation globally."""
    container.register_service(interface, implementation)


async def resolve(interface: Type[T]) -> T:
    """Resolve an instance globally."""
    return await container.resolve(interface)