from __future__ import annotations

from tests.convert.solidworks.research.Curve.Fields.AssertBytes import AssertBytes
from tests.convert.solidworks.research.Curve.Fields.AssertContext import AssertContext
from tests.convert.solidworks.research.Curve.Fields.AssertFloat import AssertFloat
from tests.convert.solidworks.research.Curve.Fields.AssertInteger import AssertInteger


# complete scalar and reference contracts make graph truncation and numeric corruption observable
def AssertValue(
    Value: dict[str, object],
    Nodes: dict[str, dict[str, object]],
    Streams: dict[str, dict[str, object]],
) -> None:
    AssertContext(Value["context"], Nodes, Streams)
    KindName = Value["type"]
    if KindName == "reference":
        assert set(Value) == {"type", "target_id", "context"}
        assert Value["target_id"] in Nodes
    elif KindName == "external-object-reference":
        assert set(Value) == {
            "type",
            "archive_index",
            "resolution",
            "target_id",
            "context",
        }
        assert AssertInteger(Value["archive_index"]) > 0
        assert Value["resolution"] == "unresolved"
        assert Value["target_id"] is None
    elif KindName == "int":
        assert set(Value) == {"type", "value", "decimal", "context"}
        _ = AssertInteger(Value)
    elif KindName == "float":
        AssertFloat(Value)
    elif KindName == "bytes":
        AssertBytes(Value)
    elif KindName in {"str", "bool", "null"}:
        assert set(Value) == {"type", "value", "context"}
        if KindName == "str":
            assert type(Value["value"]) is str
        elif KindName == "bool":
            assert type(Value["value"]) is bool
        else:
            assert Value["value"] is None
    else:
        raise AssertionError(f"unrecognized inventory value kind {KindName!r}")
