from __future__ import annotations

from typing import Protocol


class ProjectChangeNotifier(Protocol):
    """Outbound port: announce that a project changed, so live views can refresh.

    A save use case calls publish() after persisting; an adapter fans the event
    out to whoever is watching the project (e.g. an open editor over SSE).
    """

    def publish(self, slug: str) -> None: ...
