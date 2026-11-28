from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertInteger import AssertInteger
from tests.Convert.Solidworks.Research.Curve.Fields.AssertMapEntry import AssertMapEntry


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
        HeaderIndex = AssertMapEntry(
            Entry, MapValue, Nodes, StreamName, Index, BaseCount
        )
        if HeaderIndex is not None:
            HeaderIndices.add(HeaderIndex)
        Values.append(MapValue)
    if StreamName == "Contents/Config-0":
        assert HeaderIndices == set(range(3, BaseCount))
    for FieldName, ExpectedKind in (("roots", "list"), ("loader_context", "dict")):
        Reference = CastValue(dict[str, object], Document[FieldName])
        assert Reference["type"] == "reference"
        assert Nodes[CastValue(str, Reference["target_id"])]["type"] == ExpectedKind
    return Values
