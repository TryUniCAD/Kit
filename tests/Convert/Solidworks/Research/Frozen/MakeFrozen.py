from __future__ import annotations

from pathlib import Path as FilePath, PurePosixPath as PosixPath
from subprocess import run as RunProcess
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Frozen.ReadFrozen import ReadFrozen
from tests.Convert.Solidworks.Research.Frozen.ReadGitSource import ReadGitSource


# historical runs must contain only reviewed source objects and no saved native payloads
def MakeFrozen(
    SourceRoot: FilePath, Inventory: dict[str, object] | None = None
) -> None:
    Manifest = ReadFrozen() if Inventory is None else Inventory
    Revision = CastValue(str, Manifest["source_revision"])
    Outcome = RunProcess(
        ["git", "rev-parse", Revision + "^{tree}"],
        cwd=KRepoRoot,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert Outcome.stdout.strip() == Manifest["source_tree"]
    Entries = CastValue(list[dict[str, object]], Manifest["files"])
    assert len(Entries) == Manifest["source_file_count"]
    for NameValue, RawValue in ReadGitSource(Entries).items():
        RelativePath = PosixPath(NameValue)
        assert not RelativePath.is_absolute() and ".." not in RelativePath.parts
        assert "\\" not in NameValue
        assert RelativePath.suffix == ".py" or NameValue == "uv.lock"
        SourcePath = SourceRoot / RelativePath
        assert SourcePath.resolve().is_relative_to(SourceRoot.resolve())
        SourcePath.parent.mkdir(parents=True, exist_ok=True)
        Written = SourcePath.write_bytes(RawValue)
        assert Written == len(RawValue)
    assert sum(PathValue.is_file() for PathValue in SourceRoot.rglob("*")) == len(
        Entries
    )
