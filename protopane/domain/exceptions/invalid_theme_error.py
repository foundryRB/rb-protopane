"""Raised when a theme save deviates from the canonical token set."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["InvalidThemeError"]


class InvalidThemeError(ProtopaneError):
    def __init__(self, violations: list[str]) -> None:
        report = "\n".join(f"- {v}" for v in violations)
        super().__init__(
            f"Theme rejected: a save replaces the whole token set, so it must carry "
            f"every canonical token with a well-formed value.\n{report}"
        )
        self.violations = violations
