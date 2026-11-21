from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus
from tests.Convert.Solidworks.Research.Curve.Fields.AssertDigest import AssertDigest


# failed file records need exact provenance without leaking opaque decoder error payloads
def AssertFailFile(
    FileData: dict[str, object],
    Expected: dict[str, str],
    Pattern: str,
    StreamName: str,
    FailureKind: str,
) -> None:
    FileName = CastValue(str, FileData["name"])
    FileEntry = FilePath(CastValue(str, FileData["path"]))
    ExpectedPath = (
        FilePath(Pattern)
        if FailureKind == "TruncatedFixture"
        else KCurveCorpus / FileName
    )
    assert FileEntry.resolve() == ExpectedPath.resolve()
    assert AssertDigest(FileData["sha256"]) == Expected[FileName]
    assert FileData["bytes"] == FileEntry.stat().st_size
    assert FileData["passed"] is False and FileData["stage"] == "container"
    assert CastValue(dict[str, object], FileData["stream"])["name"] == StreamName
    assert FileData.get("proven_schemas") is not True
    assert "document" not in FileData and "nodes" not in FileData
    ErrorData = CastValue(dict[str, object], FileData["error"])
    assert set(ErrorData) == {"type", "message_sha256", "message_policy"}
    assert isinstance(ErrorData["type"], str) and ErrorData["type"]
    _ = AssertDigest(ErrorData["message_sha256"])
    assert ErrorData["message_policy"] == (
        "hashed to avoid dumping opaque payloads through codec exceptions"
    )
