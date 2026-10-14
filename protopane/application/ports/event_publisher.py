from __future__ import annotations

from typing import Protocol


class EventPublisher(Protocol):
    """Outbound port: state one past-tense fact about this hub's own domain on the bus.

    The contract is REF-Events. An implementation MUST NOT raise, block past a
    short bound, or otherwise change the outcome of the act that caused the
    publish (section 6): a publish that cannot be delivered is dropped and
    logged, and no save or export depends on a broker. ``event_type`` is one
    row of the hub's own vocabulary (``application/events.py``), never composed
    at the call site; ``subject`` is the project slug; ``data`` carries
    identity and pointers, never a screen's markup or a theme's token values.

    Distinct from ``ProjectChangeNotifier``, which fans a change out to the
    editors watching one project over SSE; that is the live view's refresh
    signal (REF-Realtime), this is the platform-wide fact.
    """

    def publish(self, *, event_type: str, subject: str, data: dict[str, object]) -> None: ...
