from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath


def FindScope(PathValues: Sequence[str]) -> tuple[FilePath, ...]:
    return tuple(
        FilePath(PathValue).resolve()
        for PathValue in PathValues
        if FilePath(PathValue).is_dir()
    )
