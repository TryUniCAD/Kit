from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertInteger import AssertInteger
from tests.Convert.Solidworks.Research.Curve.Fields.AssertPosition import AssertPosition


# object records need complete fields and archive provenance before their references are trusted
def AssertObjNode(
    NodeData: dict[str, object], Streams: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
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
    Values = [CastValue(dict[str, object], NodeData["schema"])]
    for FieldData in Fields:
        assert set(FieldData) == {"name", "value"}
        Values.extend(
            (
                CastValue(dict[str, object], FieldData["name"]),
                CastValue(dict[str, object], FieldData["value"]),
            )
        )
    OriginValue = NodeData["archive_origin"]
    if OriginValue is not None:
        assert isinstance(OriginValue, dict)
        OriginData = CastValue(dict[str, object], OriginValue)
        assert OriginData["stream"] in Streams
        assert AssertInteger(OriginData["archive_index"]) > 0
    if NodeData["archive_index"] is not None:
        assert AssertInteger(NodeData["archive_index"]) > 0
    AssertPosition(NodeData, Streams)
    return Values
