"""Raised when markup carries literal colors instead of design tokens."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["OffTokenMarkupError"]


class OffTokenMarkupError(ProtopaneError):
    def __init__(self, subject: str, violations: list[str]) -> None:
        report = "\n".join(f"- {v}" for v in violations)
        super().__init__(
            f"{subject} rejected: markup must stay token-backed so it "
            f"reskins with the brand and survives handoff.\n{report}"
        )
        self.subject = subject
        self.violations = violations
