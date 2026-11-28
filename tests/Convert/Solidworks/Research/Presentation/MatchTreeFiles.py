from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue


# unseen tree predictions require every constructor input and automatic source membership to remain frozen
def MatchTreeFiles(Freeze: dict[str, object], SourceRoot: FilePath) -> None:
    Entries = CastValue(list[dict[str, object]], Freeze["files"])
    assert Freeze["constructor_dependency_count"] == len(Entries) == 3435
    for Entry in Entries:
        SourcePath = SourceRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(SourceRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    SourceNames = {CastValue(str, Entry["path"]) for Entry in Entries}
    SourceDir = SourceRoot / CastValue(str, Freeze["automatic_source_directory"])
    assert {
        SourcePath.relative_to(SourceRoot).as_posix()
        for SourcePath in SourceDir.rglob("*.py")
    } == {NameValue for NameValue in SourceNames if NameValue.startswith("src/")}
    SchemaPath = SourceRoot / CastValue(str, Freeze["schema_directory"])
    assert (
        sorted(SourcePath.name for SourcePath in SchemaPath.glob("*.py"))
        == Freeze["schema_membership"]
    )
