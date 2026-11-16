from __future__ import annotations

from hashlib import sha256 as HashBytes
from math import isfinite as IsFinite, isnan as IsNan
from struct import pack as PackValue, unpack as UnpackValue
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertContext import AssertContext
from tests.convert.solidworks.research.Curve.Fields.AssertDigest import AssertDigest
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
        AssertInteger(Value)
    elif KindName == "float":
        assert set(Value) == {
            "type",
            "value",
            "hex",
            "finite",
            "context",
            "decoded_python_binary64_be",
        }
        HexText = Value["hex"]
        BitsText = Value["decoded_python_binary64_be"]
        assert isinstance(HexText, str)
        assert isinstance(BitsText, str) and len(BitsText) == 16
        BitBytes = bytes.fromhex(BitsText)
        assert len(BitBytes) == 8 and BitBytes.hex() == BitsText
        BitValue = UnpackValue(">d", BitBytes)[0]
        HexValue = float.fromhex(HexText)
        assert type(Value["finite"]) is bool
        assert Value["finite"] is IsFinite(BitValue)
        if IsNan(BitValue):
            assert IsNan(HexValue)
            assert Value["value"] == HexText == "nan"
        else:
            assert PackValue(">d", HexValue) == BitBytes
            assert BitValue.hex() == HexText
            if IsFinite(BitValue):
                assert type(Value["value"]) is float
                assert PackValue(">d", CastValue(float, Value["value"])) == BitBytes
            else:
                assert Value["value"] == HexText
    elif KindName == "bytes":
        assert set(Value) == {"type", "bytes", "sha256", "context"}
        assert type(Value["bytes"]) is int
        assert CastValue(int, Value["bytes"]) >= 0
        ByteHash = AssertDigest(Value["sha256"])
        if Value["bytes"] == 0:
            assert ByteHash == HashBytes(b"").hexdigest()
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
