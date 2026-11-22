from __future__ import annotations

from os import getenv as ReadEnv
from pathlib import Path as FilePath

from convert.Security.PathBoundary import UnsafePath
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import (
    ArtifactLeaf,
    CheckArtifact,
)


# a report subdirectory must retain its declared location under the chosen root
def BoundDir(RootPath: FilePath, Parts: tuple[str, ...]) -> FilePath:
    OutputRoot = CheckArtifact(RootPath)
    TargetPath = OutputRoot.joinpath(*(ArtifactLeaf(PartName) for PartName in Parts))
    ActualPath = CheckArtifact(TargetPath)
    if ActualPath != TargetPath:
        raise UnsafePath("research artifact directory resolves to a different location")
    return ActualPath


# pytest temporary ownership supplies the default when no artifact route was selected
def ReportDir(TmpPath: FilePath, *Parts: str) -> FilePath:
    return BoundDir(FilePath(ReadEnv("SwResearchOutput") or TmpPath), Parts)


# native candidate files belong only to the explicit artifact workflow
def CandidateDir(*Parts: str) -> FilePath | None:
    OutputPath = ReadEnv("SwResearchOutput")
    return None if OutputPath is None else BoundDir(FilePath(OutputPath), Parts)
