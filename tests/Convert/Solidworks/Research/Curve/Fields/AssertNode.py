from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertContext import AssertContext
from tests.Convert.Solidworks.Research.Curve.Fields.AssertObjNode import AssertObjNode


# explicit node ownership and lengths expose missing fields without reconstructing serializer logic
def AssertNode(
    NodeData: dict[str, object],
    Nodes: dict[str, dict[str, object]],
    Streams: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    AssertContext(NodeData["first_seen"], Nodes, Streams)
    KindName = NodeData["type"]
    Values: list[dict[str, object]] = []
    if KindName == "object":
        return AssertObjNode(NodeData, Streams)
    elif KindName == "dict":
        assert set(NodeData) == {"id", "type", "first_seen", "length", "entries"}
        Entries = CastValue(list[dict[str, object]], NodeData["entries"])
        assert type(NodeData["length"]) is int
        assert NodeData["length"] == len(Entries)
        for Entry in Entries:
            assert set(Entry) == {"key", "value"}
            Values.extend(
                (
                    CastValue(dict[str, object], Entry["key"]),
                    CastValue(dict[str, object], Entry["value"]),
                )
            )
    else:
        assert KindName in {"list", "tuple"}
        assert set(NodeData) == {"id", "type", "first_seen", "length", "items"}
        Items = CastValue(list[dict[str, object]], NodeData["items"])
        assert type(NodeData["length"]) is int
        assert NodeData["length"] == len(Items)
        Values.extend(Items)
    return Values
