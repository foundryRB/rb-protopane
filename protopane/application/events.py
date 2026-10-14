"""The facts this hub states on the platform event bus, and the one way to state one.

REF-Events gives each domain exactly one owner, and this hub owns ``prototyping``
by its grant. The constants below are its whole vocabulary; the docs page
``events.md`` states the same rows for consumers, and a test holds the two equal
so neither can drift (REF-Events section 3: each owner states its own types,
held by its own tests). A type is never composed at a call site. No screen
markup and no token value enters an event: the instance stays the store, and a
reader fetches by slug.

``state_fact`` is where the one-way rule is enforced for every caller at once.
A publisher is contractually forbidden from raising, but a caller that trusted
that contract and was wrong would fail the save it had already committed, which
is the single failure REF-Events section 6 exists to prevent. So the guarantee
is made true here rather than assumed.
"""

from __future__ import annotations

from protopane.application.ports.event_publisher import EventPublisher
from protopane.logging import get_logger

__all__ = [
    "PROJECT_ARCHIVED",
    "PROJECT_CREATED",
    "PROJECT_DELETED",
    "PROJECT_EXPORTED",
    "PROJECT_RENAMED",
    "PROJECT_UNARCHIVED",
    "SCHEME_DELETED",
    "SCHEME_SAVED",
    "SCREEN_DELETED",
    "SCREEN_SAVED",
    "THEME_SAVED",
    "state_fact",
]

logger = get_logger(__name__)

# The prototyping domain: the projects this hub holds, their themes, schemes, and screens.
PROJECT_CREATED = "com.foundry.prototyping.project.created"
THEME_SAVED = "com.foundry.prototyping.theme.saved"
SCHEME_SAVED = "com.foundry.prototyping.scheme.saved"
SCHEME_DELETED = "com.foundry.prototyping.scheme.deleted"
SCREEN_SAVED = "com.foundry.prototyping.screen.saved"
SCREEN_DELETED = "com.foundry.prototyping.screen.deleted"
PROJECT_EXPORTED = "com.foundry.prototyping.project.exported"
PROJECT_RENAMED = "com.foundry.prototyping.project.renamed"
PROJECT_ARCHIVED = "com.foundry.prototyping.project.archived"
PROJECT_UNARCHIVED = "com.foundry.prototyping.project.unarchived"
PROJECT_DELETED = "com.foundry.prototyping.project.deleted"


def state_fact(
    publisher: EventPublisher | None,
    *,
    event_type: str,
    subject: str,
    data: dict[str, object],
) -> None:
    """Publish a fact, and let nothing about it reach the caller.

    Every failure mode ends the same way: dropped, logged at warning, and the
    act that caused it completes with the outcome it already had. No publisher
    wired (a hub with no bus grant) states nothing.
    """
    if publisher is None:
        return
    try:
        publisher.publish(event_type=event_type, subject=subject, data=data)
    except Exception as exc:  # noqa: BLE001 - a publish never fails its cause
        logger.warning("dropped event %s for %s: %s", event_type, subject, exc)
