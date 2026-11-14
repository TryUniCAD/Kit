from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath


def IsCovered(RootText: str, ScopeList: Sequence[PurePosixPath]) -> bool:
    RootParts = PurePosixPath(RootText).parts
    return any(
        RootParts[: len(ScopePath.parts)] == ScopePath.parts for ScopePath in ScopeList
    )
