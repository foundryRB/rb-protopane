from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Theme:
    """A brand's design tokens: token name -> CSS value, e.g. --primary -> '217 91% 60%'."""

    tokens: dict[str, str] = field(default_factory=dict)

    def to_css(self) -> str:
        """Render the tokens as a :root rule, ready to drop into a stylesheet."""
        body = "\n".join(f"  {name}: {value};" for name, value in self.tokens.items())
        return f":root {{\n{body}\n}}\n"
