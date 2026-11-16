from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.CorpusPaths import KCurveCorpus
from tests.convert.solidworks.research.Curve.Fields.AssertDigest import AssertDigest
from tests.convert.solidworks.research.Curve.Fields.AssertGraph import AssertGraph
from tests.convert.solidworks.research.Curve.Fields.AssertLoadUse import AssertLoadUse
from tests.convert.solidworks.research.Curve.Fields.AssertSources import AssertSources


# source fingerprints and completed admission must precede any field graph success claim
def AssertFieldFile(
    Report: dict[str, object],
    Entry: dict[str, object],
    StreamName: str,
    IsLinked: bool,
) -> dict[str, int]:
    FileName = CastValue(str, Entry["file"])
    assert Report["name"] == FileName
    FileEntry = KCurveCorpus / FileName
    assert FilePath(CastValue(str, Report["path"])).resolve() == FileEntry.resolve()
    assert AssertDigest(Report["sha256"]) == Entry["sha256"]
    assert Report["bytes"] == FileEntry.stat().st_size
    assert Report["passed"] is Report["proven_schemas"] is True
    assert Report["stage"] == "complete" and "error" not in Report
    Streams = {
        CastValue(str, Stream["name"]): Stream
        for Stream in CastValue(list[dict[str, object]], Entry["streams"])
    }
    StreamData = CastValue(dict[str, object], Report["stream"])
    assert StreamData["name"] == StreamName
    assert StreamData["tail"] == 0
    assert StreamData["bytes"] == Streams[StreamName]["bytes"]
    assert AssertDigest(StreamData["sha256"]) == Streams[StreamName]["sha256"]
    UsageData = CastValue(dict[str, object], Report["schema_usage"])
    SourceNames = AssertLoadUse(UsageData, Streams, StreamName, IsLinked)
    AssertSources(Report, Streams, SourceNames, StreamName, IsLinked)
    return AssertGraph(Report, Streams, StreamName, IsLinked)
