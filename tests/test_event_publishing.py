"""INT-PP-B35: publishing is one-way. With the bus unreachable, every act that would
publish completes with the same outcome, the same result, and the same state on disk
as it does with the bus up, each dropped publish is logged, and every fact is one row
of the hub's own events page."""

from __future__ import annotations

import json
import logging
import re
from contextlib import contextmanager
from pathlib import Path

import pytest
from pytest_intent import intent

from protopane.adapters.outbound.events.publisher import SOURCE, LoggingEventPublisher, cloud_event
from protopane.application import events as vocabulary
from protopane.application.events import (
    PROJECT_ARCHIVED,
    PROJECT_CREATED,
    PROJECT_DELETED,
    PROJECT_EXPORTED,
    PROJECT_RENAMED,
    PROJECT_UNARCHIVED,
    SCHEME_DELETED,
    SCHEME_SAVED,
    SCREEN_DELETED,
    SCREEN_SAVED,
    THEME_SAVED,
    state_fact,
)
from protopane.container import Container
from protopane.domain.constants import DEFAULT_THEME_TOKENS


class RecordingPublisher:
    """A bus that is up. It builds the real envelope before recording, so a payload
    the adapter could not serialize fails here instead of being dropped in production."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str, dict]] = []

    def publish(self, *, event_type, subject, data) -> None:
        cloud_event(event_type=event_type, subject=subject, data=data)
        self.published.append((event_type, subject, data))

    @property
    def types(self) -> list[str]:
        return [t for t, _s, _d in self.published]


class RaisingPublisher:
    """A bus that is down in the least forgiving way: every publish explodes."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def publish(self, *, event_type, subject, data) -> None:
        self.attempts.append(event_type)
        raise ConnectionError("bus unreachable")


@contextmanager
def captured_warnings():
    """Collect the hub's own warnings: its logger namespace does not propagate, so a
    handler on that namespace is how a test sees them."""
    records: list[logging.LogRecord] = []

    class Sink(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    sink = Sink(level=logging.WARNING)
    logger = logging.getLogger("protopane")
    logger.addHandler(sink)
    try:
        yield records
    finally:
        logger.removeHandler(sink)


def _container(root: Path, events) -> Container:
    return Container(
        projects_dir=root / "projects", templates_dir=root / "templates", events=events
    )


def _tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


TOKENS = dict(DEFAULT_THEME_TOKENS)


# Each act: creates what it needs, performs the act, returns something comparable.
def _create(c: Container):
    return c.create_project("Acme").slug


def _theme(c: Container):
    slug = c.create_project("Acme").slug
    return c.save_theme(slug, TOKENS).theme.tokens


def _scheme(c: Container):
    slug = c.create_project("Acme").slug
    return [s.slug for s in c.save_scheme(slug, "dark", "Dark", TOKENS).schemes]


def _delete_scheme(c: Container):
    slug = c.create_project("Acme").slug
    c.save_scheme(slug, "dark", "Dark", TOKENS)
    return [s.slug for s in c.delete_scheme(slug, "dark").schemes]


def _screen(c: Container):
    slug = c.create_project("Acme").slug
    return [s.slug for s in c.save_screen(slug, "home", "Home", "<h1>Hi</h1>", "").screens]


def _delete_screen(c: Container):
    slug = c.create_project("Acme").slug
    c.save_screen(slug, "about", "About", "<h1>About</h1>", "")
    return [s.slug for s in c.delete_screen(slug, "about").screens]


def _export(c: Container):
    slug = c.create_project("Acme").slug
    return len(c.export_project(slug).screens)


def _rename(c: Container):
    slug = c.create_project("Acme").slug
    return c.rename_project(slug, new_slug="acme-two", new_name="Acme Two").slug


def _archive(c: Container):
    slug = c.create_project("Acme").slug
    return c.archive_project(slug).archived


def _unarchive(c: Container):
    slug = c.create_project("Acme").slug
    c.archive_project(slug)
    return c.unarchive_project(slug).archived


def _delete(c: Container):
    slug = c.create_project("Acme").slug
    c.delete_project(slug)
    return [p.slug for p in c.list_projects()]


_ACTS = [
    pytest.param(_create, [PROJECT_CREATED], id="create"),
    pytest.param(_theme, [PROJECT_CREATED, THEME_SAVED], id="theme"),
    pytest.param(_scheme, [PROJECT_CREATED, SCHEME_SAVED], id="scheme"),
    pytest.param(
        _delete_scheme, [PROJECT_CREATED, SCHEME_SAVED, SCHEME_DELETED], id="delete-scheme"
    ),
    pytest.param(_screen, [PROJECT_CREATED, SCREEN_SAVED], id="screen"),
    pytest.param(
        _delete_screen, [PROJECT_CREATED, SCREEN_SAVED, SCREEN_DELETED], id="delete-screen"
    ),
    pytest.param(_export, [PROJECT_CREATED, PROJECT_EXPORTED], id="export"),
    pytest.param(_rename, [PROJECT_CREATED, PROJECT_RENAMED], id="rename"),
    pytest.param(_archive, [PROJECT_CREATED, PROJECT_ARCHIVED], id="archive"),
    pytest.param(
        _unarchive, [PROJECT_CREATED, PROJECT_ARCHIVED, PROJECT_UNARCHIVED], id="unarchive"
    ),
    pytest.param(_delete, [PROJECT_CREATED, PROJECT_DELETED], id="delete"),
]


@intent("INT-PP-B35")
@pytest.mark.parametrize(("act", "facts"), _ACTS)
def test_every_act_is_identical_with_the_bus_down(tmp_path: Path, act, facts) -> None:
    up_root, down_root = tmp_path / "up", tmp_path / "down"

    up = RecordingPublisher()
    result_up = act(_container(up_root, up))
    assert up.types == facts
    for _t, subject, data in up.published:
        assert subject
        assert json.dumps(data)
        # Pointers, never the markup or the token values (REF-Events section 5).
        assert "html" not in data and "css" not in data
        assert not any(isinstance(v, dict) for v in data.values())

    down = RaisingPublisher()
    with captured_warnings() as warnings:
        result_down = act(_container(down_root, down))
    assert down.attempts == facts, "the act must still attempt each publish"
    assert result_down == result_up
    assert _tree(up_root) == _tree(down_root)
    for fact in facts:
        assert any(fact in r.getMessage() for r in warnings), f"a dropped {fact} must be logged"


@intent("INT-PP-B35")
def test_state_fact_never_raises_and_no_publisher_states_nothing():
    with captured_warnings() as warnings:
        state_fact(RaisingPublisher(), event_type=PROJECT_CREATED, subject="acme", data={})
    assert any(PROJECT_CREATED in r.getMessage() for r in warnings)
    state_fact(None, event_type=PROJECT_CREATED, subject="acme", data={})


@intent("INT-PP-B35")
def test_the_envelope_is_a_cloudevent_carrying_pointers_not_payloads():
    raw = cloud_event(event_type=SCREEN_SAVED, subject="acme", data={"project": "acme"})
    event = json.loads(raw)
    assert event["specversion"] == "1.0"
    assert event["type"] == SCREEN_SAVED
    assert event["subject"] == "acme"
    assert event["source"] == SOURCE
    assert event["datacontenttype"] == "application/json"
    assert event["id"] and event["time"]
    other = json.loads(cloud_event(event_type=SCREEN_SAVED, subject="acme", data={}))
    assert other["id"] != event["id"]
    with pytest.raises(TypeError):
        cloud_event(event_type=SCREEN_SAVED, subject="acme", data={"screen": object()})
    LoggingEventPublisher().publish(
        event_type=SCREEN_SAVED, subject="acme", data={"screen": object()}
    )


_EVENTS_PAGE = Path(__file__).resolve().parents[1] / "docs/src/content/docs/events.md"


@intent("INT-PP-B35")
def test_the_events_page_states_exactly_the_types_the_hub_emits():
    """REF-Events section 3: each owner states its own types on its own page, held
    against the publisher by its own tests."""
    emitted = {
        value
        for name, value in vars(vocabulary).items()
        if name.isupper() and isinstance(value, str) and value.startswith("com.foundry.")
    }
    assert emitted
    assert {v.split(".")[2] for v in emitted} == {"prototyping"}
    page = _EVENTS_PAGE.read_text(encoding="utf-8")
    stated = set(re.findall(r"^\| `(com\.foundry\.[a-z.]+)` \|", page, flags=re.M))
    assert stated == emitted, (
        f"page states {sorted(stated - emitted)} the hub never emits; "
        f"hub emits {sorted(emitted - stated)} the page never states"
    )
