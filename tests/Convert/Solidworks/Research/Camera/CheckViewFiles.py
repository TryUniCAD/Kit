from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# constructor integrity must cover shared dependencies and automatic schema membership without reading source cad files
def CheckViewFiles(Freeze: dict[str, object], BaseFreeze: dict[str, object]) -> None:
    Entries = CastValue(list[dict[str, object]], Freeze["files"])
    assert Freeze["constructor_dependency_count"] == len(Entries) == 354
    assert {
        RowValue["path"]
        for RowValue in CastValue(list[dict[str, object]], BaseFreeze["files"])
    }.issubset({RowValue["path"] for RowValue in Entries})
    for Entry in Entries:
        SourcePath = KRepoRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(KRepoRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    SchemaPath = KRepoRoot / CastValue(str, Freeze["schema_directory"])
    assert (
        sorted(SourcePath.name for SourcePath in SchemaPath.glob("*.py"))
        == Freeze["schema_membership"]
    )
