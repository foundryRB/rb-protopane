from __future__ import annotations

from dataclasses import dataclass, field

from protopane.domain.exceptions.last_screen_error import LastScreenError
from protopane.domain.exceptions.scheme_not_found_error import SchemeNotFoundError
from protopane.domain.exceptions.screen_not_found_error import ScreenNotFoundError
from protopane.domain.model.design_system_ref import DesignSystemRef
from protopane.domain.model.scheme import Scheme
from protopane.domain.model.screen import Screen
from protopane.domain.model.theme import Theme


@dataclass
class Project:
    """A client prototype: a brand theme plus the screens built against it. Identity is the slug.

    `schemes` are the pre-configured palette options the customer flips between; the live
    `theme` is whichever one is currently applied (or a hand-tuned variant of it).
    `design_system` records which packaged system the identity was seeded from (guidance
    snapshotted verbatim); hand-tuning the theme afterwards keeps the provenance.

    An archived project keeps all its data but is parked out of the default listing.
    """

    slug: str
    name: str
    theme: Theme
    screens: list[Screen] = field(default_factory=list)
    schemes: list[Scheme] = field(default_factory=list)
    design_system: DesignSystemRef | None = None
    archived: bool = False

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme

    def record_design_system(self, ref: DesignSystemRef) -> None:
        self.design_system = ref

    def archive(self) -> None:
        self.archived = True

    def unarchive(self) -> None:
        self.archived = False

    def upsert_scheme(self, scheme: Scheme) -> None:
        """Replace the scheme with the same slug, or append it if new."""
        self.schemes = [s for s in self.schemes if s.slug != scheme.slug] + [scheme]

    def remove_scheme(self, scheme_slug: str) -> None:
        """Remove the scheme by slug; unknown slug raises SchemeNotFoundError."""
        if self.scheme(scheme_slug) is None:
            raise SchemeNotFoundError(self.slug, scheme_slug)
        self.schemes = [s for s in self.schemes if s.slug != scheme_slug]

    def scheme(self, slug: str) -> Scheme | None:
        return next((s for s in self.schemes if s.slug == slug), None)

    def upsert_screen(self, screen: Screen) -> None:
        """Replace the screen with the same slug, or append it if new."""
        for i, s in enumerate(self.screens):
            if s.slug == screen.slug:
                self.screens[i] = screen
                return
        self.screens.append(screen)

    def remove_screen(self, screen_slug: str) -> None:
        """Remove the screen by slug. A project keeps at least one screen."""
        if self.screen(screen_slug) is None:
            raise ScreenNotFoundError(self.slug, screen_slug)
        if len(self.screens) == 1:
            raise LastScreenError(self.slug, screen_slug)
        self.screens = [s for s in self.screens if s.slug != screen_slug]

    def screen(self, slug: str) -> Screen | None:
        return next((s for s in self.screens if s.slug == slug), None)
