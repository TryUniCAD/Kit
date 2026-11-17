from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertInteger import AssertInteger


# archive map identities must survive reporting instead of losing their native tuple tags
def AssertDocument(
    Document: dict[str, object],
    Nodes: dict[str, dict[str, object]],
    StreamName: str,
) -> list[dict[str, object]]:
    assert Document["stream"] == StreamName
    BaseCount = AssertInteger(Document["map_base"])
    MapCount = AssertInteger(Document["map_count"])
    assert MapCount >= BaseCount >= 1
    Values = [
        CastValue(dict[str, object], Document[FieldName])
        for FieldName in ("head", "roots", "loader_context")
    ]
    SeenIndices: set[int] = set()
    HeaderIndices: set[int] = set()
    for Entry in CastValue(list[dict[str, object]], Document["archive_map"]):
        Index = AssertInteger(Entry["index"])
        assert 1 <= Index < MapCount and Index not in SeenIndices
        SeenIndices.add(Index)
        MapValue = CastValue(dict[str, object], Entry["value"])
        assert MapValue["type"] == "reference"
        Target = Nodes[CastValue(str, MapValue["target_id"])]
        if Entry["kind"] == "class":
            assert Target["type"] == "tuple" and Target["length"] == 3
            Items = CastValue(list[dict[str, object]], Target["items"])
            assert Items[0]["type"] == "str" and Items[0]["value"] == "class"
            assert Items[1]["type"] == "str" and Items[1]["value"]
        else:
            assert Entry["kind"] == "obj" and Target["type"] == "object"
            OriginData = CastValue(dict[str, object], Target["archive_origin"])
            OriginIndex = AssertInteger(OriginData["archive_index"])
            assert AssertInteger(Target["archive_index"]) == OriginIndex
            if OriginData[
                "stream"
            ] == "Contents/Config-0-ModelHeader" and StreamName in {
                "Contents/Config-0",
                "Contents/Config-0-ResolvedFeatures",
            }:
                assert 3 <= Index < BaseCount
                assert Target["position_stream"] == OriginData["stream"]
                HeaderIndices.add(Index)
            else:
                assert OriginIndex == Index
        Values.append(MapValue)
    if StreamName == "Contents/Config-0":
        assert HeaderIndices == set(range(3, BaseCount))
    for FieldName, ExpectedKind in (("roots", "list"), ("loader_context", "dict")):
        Reference = CastValue(dict[str, object], Document[FieldName])
        assert Reference["type"] == "reference"
        assert Nodes[CastValue(str, Reference["target_id"])]["type"] == ExpectedKind
    return Values
