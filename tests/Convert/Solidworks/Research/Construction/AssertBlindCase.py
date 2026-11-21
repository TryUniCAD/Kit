from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive


# generated native files must retain computed parameters aliases and stream bytes across the sdk boundary
def AssertBlindCase(Report: dict[str, object], DepthValue: float) -> int:
    assert Report["depth_m"] == DepthValue
    assert Report["parameter_names"] == ["D1", "D2", "D3", "D4", "D19"]
    assert (
        Report["parameter_node_ids"] == [-1] * 5 and Report["retained_from_end"] is True
    )
    DimensionIds = CastValue(list[int], Report["dimension_ids"])
    assert len(set(DimensionIds)) == 5 and all(
        NativeId >= 0 for NativeId in DimensionIds
    )
    StreamValues = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert set(StreamValues) == {
        "Contents/CMgr",
        "Contents/Config-0",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0-ResolvedFeatures",
        "Header2",
    }
    assert all(
        RowValue["same_as_fresh_research_graph"] for RowValue in StreamValues.values()
    )
    assert all(
        RowValue["rejected"]
        for RowValue in CastValue(list[dict[str, object]], Report["malformed"])
    )
    UsageValue = CastValue(dict[str, object], Report["resolved_usage"])
    assert (
        UsageValue["completed"] is True
        and not UsageValue["missing_schemas"]
        and not UsageValue["provisional_schemas"]
    )
    assert {"moEndSpec_c", "moLengthParameter_c", "moAngleParameter_c"}.issubset(
        CastValue(list[str], UsageValue["used_schemas"])
    )
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    assert (
        len(BlobValue) == Report["bytes"]
        and HashBytes(BlobValue).hexdigest() == Report["sha256"]
    )
    Archive = SldprtArchive.from_bytes(BlobValue)
    for StreamName, RowValue in StreamValues.items():
        BufferValue = Archive.require(StreamName)
        assert (
            len(BufferValue) == RowValue["bytes"]
            and HashBytes(BufferValue).hexdigest() == RowValue["sha256"]
        )
    return CastValue(int, StreamValues["Contents/Config-0-ResolvedFeatures"]["bytes"])
