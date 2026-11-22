from __future__ import annotations

from os import getenv as ReadEnv
from os.path import abspath as AbsolutePath
from pathlib import Path as FilePath
from tempfile import gettempdir as GetTempDir

from convert.Security.PathBoundary import ResolveWithin, UnsafePath
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# hosted artifacts live in the temporary directory managed by the runner
def HostedRoot() -> FilePath | None:
    Expected = KRepoRoot.parents[1] / "_temp"
    if ReadEnv("GITHUB_ACTIONS") != "true" or ReadEnv("RUNNER_TEMP") != str(Expected):
        return None
    if not Expected.is_dir() or Expected.resolve(strict=True) != Expected:
        raise UnsafePath("hosted research temporary root is not canonical")
    return Expected


# lexical and physical containment bind chosen paths to existing trusted authorities
def CheckArtifact(PathValue: FilePath, NeedFile: bool = False) -> FilePath:
    Candidate = FilePath(AbsolutePath(PathValue))
    Roots: tuple[FilePath, ...] = (FilePath.cwd(), KRepoRoot, FilePath(GetTempDir()))
    Hosted = HostedRoot()
    if Hosted is not None:
        Roots += (Hosted,)
    for RootPath in Roots:
        Physical = RootPath.resolve(strict=True)
        if Candidate.is_relative_to(RootPath):
            return ResolveWithin(Candidate.relative_to(RootPath), Physical, NeedFile)
        if Candidate.is_relative_to(Physical):
            return ResolveWithin(Candidate, Physical, NeedFile)
    raise UnsafePath("research path escapes the working, checkout and temporary roots")


# an authored filename component must represent a leaf even on another platform
def ArtifactLeaf(NameValue: object) -> str:
    if (
        not isinstance(NameValue, str)
        or not NameValue
        or NameValue in (".", "..")
        or any(CharValue in "/\\:\0" for CharValue in NameValue)
    ):
        raise UnsafePath("research artifact name must be a single filename")
    return NameValue


# fixed artifact locations cannot alias other files in the same output directory
def ArtifactFile(OutputDir: FilePath, NameValue: str) -> FilePath:
    ParentPath = CheckArtifact(OutputDir)
    LeafName = ArtifactLeaf(NameValue)
    TargetPath = ResolveWithin(LeafName, ParentPath)
    if TargetPath != ParentPath / LeafName:
        raise UnsafePath("research artifact filename resolves to a different file")
    return TargetPath
