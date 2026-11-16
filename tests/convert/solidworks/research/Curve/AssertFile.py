from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.AssertStream import AssertStream
from tests.convert.solidworks.research.Curve.AssertUsage import AssertUsage


# each reported stream must refer to the actual prepared file and its manifest hashes
def AssertFile(
    Report: dict[str, object],
    Entry: dict[str, object],
    Selected: tuple[str, ...],
    IsLinked: bool,
) -> None:
    StreamRows = CastValue(list[dict[str, object]], Entry["streams"])
    ManifestStreams = {
        CastValue(str, StreamData["name"]): StreamData for StreamData in StreamRows
    }
    ParsedStreams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(ManifestStreams) == len(StreamRows)
    assert Report["sha256"] == Entry["sha256"]
    assert (
        Report["passed"]
        is Report["byte_identity_passed"]
        is Report["proven_schemas"]
        is True
    )
    AssertUsage(CastValue(dict[str, object], Report["schema_usage"]))
    assert set(ParsedStreams) == set(Selected)
    for NameValue, StreamData in ParsedStreams.items():
        assert StreamData["sha256"] == ManifestStreams[NameValue]["sha256"]
        assert StreamData["bytes"] == ManifestStreams[NameValue]["bytes"]
        assert CastValue(int, StreamData["bytes"]) > 0
        AssertStream(StreamData, ManifestStreams, IsLinked)
