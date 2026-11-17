from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertInteger import AssertInteger


# direct entries need both their local slot and the native record's original position
def AssertMapEntry(
    Entry: dict[str, object],
    MapValue: dict[str, object],
    Nodes: dict[str, dict[str, object]],
    StreamName: str,
    Index: int,
    BaseCount: int,
) -> bool:
    assert MapValue["type"] == "reference"
    Target = Nodes[CastValue(str, MapValue["target_id"])]
    if Entry["kind"] == "class":
        assert Target["type"] == "tuple" and Target["length"] == 3
        Items = CastValue(list[dict[str, object]], Target["items"])
        assert Items[0]["type"] == "str" and Items[0]["value"] == "class"
        assert Items[1]["type"] == "str" and Items[1]["value"]
        return False
    assert Entry["kind"] == "obj" and Target["type"] == "object"
    Origin = CastValue(dict[str, object], Target["archive_origin"])
    OriginIndex = AssertInteger(Origin["archive_index"])
    assert AssertInteger(Target["archive_index"]) == OriginIndex
    IsHeader = Origin["stream"] == "Contents/Config-0-ModelHeader" and StreamName in {
        "Contents/Config-0",
        "Contents/Config-0-ResolvedFeatures",
    }
    if IsHeader:
        assert 3 <= Index < BaseCount
        assert Target["position_stream"] == Origin["stream"]
    else:
        assert OriginIndex == Index
    return IsHeader
