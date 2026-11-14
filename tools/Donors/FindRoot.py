from __future__ import annotations

from pathlib import PurePosixPath

from tools.Donors.ReplayRules import KRootMarkers


def FindRoot(SourcePath: PurePosixPath) -> str:
    PartList = SourcePath.parts
    for PartIndex, PartText in enumerate(PartList[:-1]):
        if PartText in KRootMarkers:
            return PurePosixPath(*PartList[:PartIndex]).as_posix()
    return SourcePath.parent.as_posix()
