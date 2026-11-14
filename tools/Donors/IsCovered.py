from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath


def IsCovered(RootText: str, ScopeList: Sequence[FilePath]) -> bool:
    RootPath = FilePath.cwd().resolve().joinpath(RootText).resolve()
    return any(RootPath.is_relative_to(ScopePath) for ScopePath in ScopeList)
