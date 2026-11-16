from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.CorpusPaths import KCurveCorpus
from tests.convert.solidworks.research.Curve.AssertSnapshot import AssertSnapshot
from tests.convert.solidworks.research.Curve.Fields.AssertDigest import AssertDigest
from tests.convert.solidworks.research.Curve.Fields.AssertGraph import AssertGraph


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
    MainLoad = CastValue(dict[str, object], UsageData["load"])
    Dependencies = CastValue(list[dict[str, object]], UsageData["dependencies"])
    assert MainLoad["role"] == "field_inventory"
    assert MainLoad["requested_stream"] == StreamName
    assert len(Dependencies) == (1 if IsLinked else 0)
    SourceNames: set[str] = set()
    for Snapshot in [MainLoad, *Dependencies]:
        AssertSnapshot(Snapshot)
        assert Snapshot["direction"] == "load"
        Calls = CastValue(list[dict[str, object]], Snapshot["schema_calls"])
        UsedSchemas = CastValue(list[str], Snapshot["used_schemas"])
        for CallData in Calls:
            assert CallData["schema"] in UsedSchemas
            assert type(CallData["count"]) is int
            assert CastValue(int, CallData["count"]) > 0
            SourceNames.update(CastValue(list[str], CallData["source_streams"]))
        RawRecords = CastValue(list[dict[str, object]], Snapshot["raw_operations"])
        assert Snapshot["raw_operation_count"] == len(RawRecords)
        for RawRecord in RawRecords:
            assert RawRecord["completed"] is True
            assert RawRecord["observed_length"] == RawRecord["declared_length"]
        if Snapshot is not MainLoad:
            assert Snapshot["role"] == "linked_map_seed"
            assert Snapshot["requested_stream"] == "Contents/Config-0"
            assert Snapshot["tail"] == 0
            assert Snapshot["bytes"] == Streams["Contents/Config-0"]["bytes"]
            assert (
                AssertDigest(Snapshot["sha256"])
                == Streams["Contents/Config-0"]["sha256"]
            )
    GraphNames = {StreamName, *(["Contents/Config-0"] if IsLinked else [])}
    GraphSeeds = CastValue(list[dict[str, object]], Report["dependencies"])
    assert len(GraphSeeds) == len(Dependencies)
    for SeedData in GraphSeeds:
        assert SeedData["name"] == "Contents/Config-0"
        assert SeedData["role"] == "linked_map_seed" and SeedData["tail"] == 0
        assert SeedData["bytes"] == Streams["Contents/Config-0"]["bytes"]
        assert (
            AssertDigest(SeedData["sha256"]) == Streams["Contents/Config-0"]["sha256"]
        )
    SourceRows = CastValue(list[dict[str, object]], Report["loader_source_streams"])
    ReportedNames = [CastValue(str, Source["name"]) for Source in SourceRows]
    assert len(ReportedNames) == len(set(ReportedNames))
    assert set(ReportedNames) == SourceNames
    for Source in SourceRows:
        NameValue = CastValue(str, Source["name"])
        assert Source["bytes"] == Streams[NameValue]["bytes"]
        assert AssertDigest(Source["sha256"]) == Streams[NameValue]["sha256"]
        assert Source["graph_included"] is (NameValue in GraphNames)
    return AssertGraph(Report, Streams, StreamName, IsLinked)
