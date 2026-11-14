from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath
from pathlib import PurePosixPath

from tools.Donors.ShowPath import ShowPath


def FindScope(PathValues: Sequence[str]) -> tuple[PurePosixPath, ...]:
    return tuple(
        PurePosixPath(ShowPath(FilePath(PathValue)))
        for PathValue in PathValues
        if FilePath(PathValue).is_dir()
    )
