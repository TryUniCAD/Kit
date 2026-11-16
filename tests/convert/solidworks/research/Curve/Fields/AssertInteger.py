from __future__ import annotations

from typing import cast as CastValue


# decimal witnesses prevent json consumers from silently losing large native integer values
def AssertInteger(Encoded: object) -> int:
    assert isinstance(Encoded, dict)
    DataValue = CastValue(dict[str, object], Encoded)
    assert DataValue["type"] == "int"
    Number = DataValue["value"]
    assert type(Number) is int
    assert DataValue["decimal"] == str(Number)
    return Number
