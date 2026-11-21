from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive


# generated polygon owners must reach real native streams with input dependent size and rejected invalid geometry
def AssertPolyBuild(Report: dict[str, object], CountValue: int) -> int:
    assert Report["point_count"] == Report["line_count"] == CountValue
    assert Report["independent_handle_count"] == CountValue * 2
    assert Report["plain_archive_nodes"] is Report["profile_backlink"] is True
    Failures = CastValue(list[dict[str, object]], Report["malformed"])
    assert len(Failures) == 14 and all(RowValue["rejected"] for RowValue in Failures)
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    assert (
        len(BlobValue) == Report["bytes"]
        and HashBytes(BlobValue).hexdigest() == Report["sha256"]
    )
    Archive = SldprtArchive.from_bytes(BlobValue)
    StreamsValue = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert set(StreamsValue) == {
        "Contents/CMgr",
        "Contents/Config-0",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0-ResolvedFeatures",
        "Header2",
    }
    for StreamName, RowValue in StreamsValue.items():
        assert RowValue["same_as_fresh_research_graph"] is True
        BufferValue = Archive.require(StreamName)
        assert (
            len(BufferValue) == RowValue["bytes"]
            and HashBytes(BufferValue).hexdigest() == RowValue["sha256"]
        )
    UsageValue = CastValue(dict[str, object], Report["resolved_usage"])
    assert (
        UsageValue["completed"] is True
        and not UsageValue["missing_schemas"]
        and not UsageValue["provisional_schemas"]
    )
    assert {"sgSketch", "sgLineHandle"}.issubset(
        CastValue(list[str], UsageValue["used_schemas"])
    )
    return CastValue(int, StreamsValue["Contents/Config-0-ResolvedFeatures"]["bytes"])
