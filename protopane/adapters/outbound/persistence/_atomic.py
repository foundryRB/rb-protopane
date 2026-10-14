from __future__ import annotations

import os
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Write text to path atomically.

    A concurrent reader sees either the previous file or the complete new one,
    never a half-written file, and a crash mid-write leaves the previous file
    intact. The temp file is created beside the target so the final rename stays
    on one filesystem (os.replace is atomic there on POSIX and Windows alike).
    """
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
