from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertDigest import AssertDigest


# retained auxiliary source receipts must distinguish graph inclusion from mere loader reads
def AssertSources(
    Report: dict[str, object],
    Streams: dict[str, dict[str, object]],
    SourceNames: set[str],
    StreamName: str,
    IsLinked: bool,
) -> None:
    GraphNames = {StreamName, *(["Contents/Config-0"] if IsLinked else [])}
    GraphSeeds = CastValue(list[dict[str, object]], Report["dependencies"])
    UsageData = CastValue(dict[str, object], Report["schema_usage"])
    Dependencies = CastValue(list[dict[str, object]], UsageData["dependencies"])
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
