from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# unseen tree predictions require every constructor input and automatic source membership to remain frozen
def MatchTreeFiles(Freeze: dict[str, object]) -> None:
    Entries = CastValue(list[dict[str, object]], Freeze["files"])
    assert Freeze["constructor_dependency_count"] == len(Entries) == 3435
    for Entry in Entries:
        SourcePath = KRepoRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(KRepoRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    SourceNames = {CastValue(str, Entry["path"]) for Entry in Entries}
    SourceDir = KRepoRoot / CastValue(str, Freeze["automatic_source_directory"])
    assert {
        SourcePath.relative_to(KRepoRoot).as_posix()
        for SourcePath in SourceDir.rglob("*.py")
    } == {NameValue for NameValue in SourceNames if NameValue.startswith("src/")}
    SchemaPath = KRepoRoot / CastValue(str, Freeze["schema_directory"])
    assert (
        sorted(SourcePath.name for SourcePath in SchemaPath.glob("*.py"))
        == Freeze["schema_membership"]
    )
