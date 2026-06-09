from __future__ import annotations

from collections import defaultdict
from typing import Callable

from app.application.events import ApplicationEvent


EventHandler = Callable[[ApplicationEvent], None]


class EventBus:
    def __init__(self):
        self._subscribers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: ApplicationEvent) -> None:
        for handler in self._subscribers.get(type(event), []):
            handler(event)
        for handler in self._subscribers.get(object, []):
            handler(event)

    def publish_many(self, events: list[ApplicationEvent]) -> None:
        for event in events:
            self.publish(event)
