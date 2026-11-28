from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# a pinned run must never fall back to project code from the editable current checkout
def MatchImports(Report: dict[str, object], SourceRoot: FilePath) -> None:
    Imports = CastValue(list[str], Report["module_reads"])
    assert Imports
    assert any(Value.startswith(str(SourceRoot / "src")) for Value in Imports)
    for Value in Imports:
        Imported = FilePath(Value)
        assert not any(
            Imported.is_relative_to(KRepoRoot / FolderName)
            for FolderName in ("src", "re", "tests")
        )
        if any(
            Marker in Value for Marker in ("/src/", "/re/tooling/sw2026/", "/tests/")
        ):
            assert Imported.is_relative_to(SourceRoot)
