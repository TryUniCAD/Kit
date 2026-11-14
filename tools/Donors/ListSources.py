from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath

KSkipFolders = frozenset({"__pycache__", ".venv", "build", "dist"})


def ShowPath(SourcePath: FilePath) -> str:
    try:
        return SourcePath.resolve().relative_to(FilePath.cwd().resolve()).as_posix()
    except ValueError:
        return SourcePath.resolve().as_posix()


def ListSources(PathValues: Sequence[str]) -> list[FilePath]:
    SourceSet: set[FilePath] = set()
    for PathValue in PathValues:
        InputPath = FilePath(PathValue)
        if not InputPath.exists():
            raise FileNotFoundError(f"path does not exist: {PathValue}")
        if InputPath.is_file():
            SourceSet.add(InputPath)
            continue
        SourceSet.update(
            SourcePath
            for SourcePath in InputPath.rglob("*.py")
            if not KSkipFolders.intersection(SourcePath.parts)
        )
    return sorted(SourceSet)
