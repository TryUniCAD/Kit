from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus
from tests.Convert.Solidworks.Research.Curve.AssertFile import AssertFile


# complete process reports must account for all expected files and stream records
def AssertReport(
    Report: dict[str, object],
    Entries: dict[str, dict[str, object]],
    Selected: tuple[str, ...],
    IsLinked: bool,
) -> None:
    Files = CastValue(list[dict[str, object]], Report["files"])
    Paths = [FilePath(CastValue(str, FileData["path"])) for FileData in Files]
    assert len(Files) == Report["file_count"] == 26
    assert len(set(Paths)) == 26
    assert {FileEntry.name for FileEntry in Paths} == set(Entries)
    assert all(
        FileEntry.resolve().parent == KCurveCorpus.resolve() for FileEntry in Paths
    )
    assert Report["version"] == 19000
    assert Report["require_proven"] is True
    assert Report["linked_configurations"] is IsLinked
    assert (
        Report["passed"]
        is Report["byte_identity_passed"]
        is Report["proven_schemas"]
        is True
    )
    assert Report["used_provisional_schemas"] == []
    for FileData, FileEntry in zip(Files, Paths, strict=True):
        AssertFile(FileData, Entries[FileEntry.name], Selected, IsLinked)
    StreamCount = sum(
        len(CastValue(dict[str, object], FileData["streams"])) for FileData in Files
    )
    assert (
        StreamCount
        == Report["stream_count"]
        == Report["passed_streams"]
        == (26 if IsLinked else 208)
    )
