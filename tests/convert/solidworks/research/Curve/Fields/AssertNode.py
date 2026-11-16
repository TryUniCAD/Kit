from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertContext import AssertContext
from tests.convert.solidworks.research.Curve.Fields.AssertInteger import AssertInteger


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
        assert set(NodeData) == {
            "id",
            "type",
            "first_seen",
            "class",
            "schema",
            "archive_origin",
            "archive_index",
            "record_start",
            "record_end",
            "position_stream",
            "field_count",
            "fields",
        }
        assert isinstance(NodeData["class"], str) and NodeData["class"]
        assert type(NodeData["field_count"]) is int
        Fields = CastValue(list[dict[str, object]], NodeData["fields"])
        assert len(Fields) == NodeData["field_count"]
        Values.append(CastValue(dict[str, object], NodeData["schema"]))
        for FieldData in Fields:
            assert set(FieldData) == {"name", "value"}
            Values.extend(
                (
                    CastValue(dict[str, object], FieldData["name"]),
                    CastValue(dict[str, object], FieldData["value"]),
                )
            )
        OriginData = NodeData["archive_origin"]
        if OriginData is not None:
            assert isinstance(OriginData, dict)
            assert OriginData["stream"] in Streams
            assert AssertInteger(OriginData["archive_index"]) > 0
        if NodeData["archive_index"] is not None:
            assert AssertInteger(NodeData["archive_index"]) > 0
        PositionStream = NodeData["position_stream"]
        StartValue, EndValue = NodeData["record_start"], NodeData["record_end"]
        if StartValue is None:
            assert PositionStream is None
        else:
            assert type(StartValue) is int and PositionStream in Streams
        for Position in (StartValue, EndValue):
            if Position is not None:
                assert type(Position) is int
                assert PositionStream in Streams
                assert (
                    0
                    <= CastValue(int, Position)
                    <= CastValue(int, Streams[CastValue(str, PositionStream)]["bytes"])
                )
        if StartValue is not None and EndValue is not None:
            assert CastValue(int, StartValue) <= CastValue(int, EndValue)
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
