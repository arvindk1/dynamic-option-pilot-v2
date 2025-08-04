"""Event bus for inter-plugin communication and system events."""

import asyncio
import logging
import weakref
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system."""

    # Plugin lifecycle events
    PLUGIN_REGISTERED = "plugin.registered"
    PLUGIN_INITIALIZED = "plugin.initialized"
    PLUGIN_ERROR = "plugin.error"
    PLUGIN_CLEANUP = "plugin.cleanup"
    PLUGIN_HEALTH_CHECK_FAILED = "plugin.health_check_failed"

    # Data events
    MARKET_DATA_RECEIVED = "data.market_data_received"
    OPTIONS_DATA_RECEIVED = "data.options_data_received"
    DATA_ERROR = "data.error"

    # Analysis events
    ANALYSIS_COMPLETED = "analysis.completed"
    SIGNAL_GENERATED = "analysis.signal_generated"
    ANALYSIS_ERROR = "analysis.error"

    # Trading events
    OPPORTUNITY_FOUND = "trading.opportunity_found"
    TRADE_EXECUTED = "trading.trade_executed"
    TRADE_ERROR = "trading.error"
    POSITION_UPDATED = "trading.position_updated"

    # Risk events
    RISK_LIMIT_EXCEEDED = "risk.limit_exceeded"
    PORTFOLIO_RISK_UPDATED = "risk.portfolio_updated"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


@dataclass
class Event:
    """Base event class."""

    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class PluginEvent(Event):
    """Plugin-specific event."""

    def __init__(
        self,
        event_type: EventType,
        plugin_name: str,
        data: Dict[str, Any] = None,
        correlation_id: str = None,
    ):
        super().__init__(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source=f"plugin.{plugin_name}",
            data=data or {},
            correlation_id=correlation_id,
        )
        self.plugin_name = plugin_name


class EventBus:
    """Async event bus for system-wide communication."""

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
        self._weak_refs = weakref.WeakSet()

    def subscribe(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        self._weak_refs.add(handler)
        logger.debug(f"Subscribed to {event_type.value}: {handler}")

    def subscribe_multiple(
        self, event_types: List[EventType], handler: Callable[[Event], None]
    ) -> None:
        """Subscribe to multiple event types with the same handler."""
        for event_type in event_types:
            self.subscribe(event_type, handler)

    def unsubscribe(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from {event_type.value}: {handler}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type.value}")

    async def emit(self, event: Event) -> None:
        """Emit an event to all subscribers."""
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # Notify subscribers
        if event.event_type in self._subscribers:
            handlers = self._subscribers[event.event_type].copy()

            # Run handlers concurrently
            tasks = []
            for handler in handlers:
                task = self._safe_handle_event(handler, event)
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Emitted event: {event.event_type.value} from {event.source}")

    async def _safe_handle_event(self, handler: Callable, event: Event) -> None:
        """Safely handle an event with error protection."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.event_type.value}: {e}")
            # Emit error event
            error_event = Event(
                event_type=EventType.SYSTEM_ERROR,
                timestamp=datetime.utcnow(),
                source="event_bus",
                data={
                    "original_event": event.event_type.value,
                    "handler": str(handler),
                    "error": str(e),
                },
            )
            # Avoid infinite recursion by not awaiting this
            asyncio.create_task(self._emit_error_event(error_event))

    async def _emit_error_event(self, error_event: Event) -> None:
        """Emit error event without triggering recursive errors."""
        try:
            async with self._lock:
                self._event_history.append(error_event)
                if len(self._event_history) > self._max_history:
                    self._event_history.pop(0)
        except Exception as e:
            logger.critical(f"Failed to emit error event: {e}")

    def get_event_history(
        self, event_type: EventType = None, limit: int = None
    ) -> List[Event]:
        """Get event history, optionally filtered by type."""
        events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if limit:
            events = events[-limit:]

        return events

    def get_subscribers_count(self, event_type: EventType = None) -> Dict[str, int]:
        """Get count of subscribers for each event type."""
        if event_type:
            return {event_type.value: len(self._subscribers.get(event_type, []))}

        return {et.value: len(handlers) for et, handlers in self._subscribers.items()}

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    async def wait_for_event(
        self,
        event_type: EventType,
        timeout: float = None,
        condition: Callable[[Event], bool] = None,
    ) -> Optional[Event]:
        """Wait for a specific event, optionally with a condition."""
        future = asyncio.Future()

        def handler(event: Event):
            if condition is None or condition(event):
                if not future.done():
                    future.set_result(event)

        self.subscribe(event_type, handler)

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self.unsubscribe(event_type, handler)

    def create_event_stream(self, event_types: List[EventType]) -> asyncio.Queue:
        """Create an async queue stream for specific event types."""
        queue = asyncio.Queue()

        def handler(event: Event):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    f"Event queue full, dropping event: {event.event_type.value}"
                )

        for event_type in event_types:
            self.subscribe(event_type, handler)

        return queue

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "total_subscribers": sum(
                len(handlers) for handlers in self._subscribers.values()
            ),
            "event_types_subscribed": len(self._subscribers),
            "history_length": len(self._event_history),
            "max_history": self._max_history,
            "subscribers_by_type": self.get_subscribers_count(),
        }
