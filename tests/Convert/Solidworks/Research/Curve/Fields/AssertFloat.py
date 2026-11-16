from __future__ import annotations

from math import isfinite as IsFinite, isnan as IsNan
from struct import pack as PackValue, unpack as UnpackValue


# decoded floating values need independent bit witnesses without implying native scalar widths
def AssertFloat(Value: dict[str, object]) -> None:
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
            assert PackValue(">d", Value["value"]) == BitBytes
        else:
            assert Value["value"] == HexText
