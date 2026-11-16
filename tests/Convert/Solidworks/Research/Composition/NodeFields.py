from __future__ import annotations

from collections.abc import Mapping
from typing import cast as CastValue


# research node fields need a checked mapping boundary before typed ownership inspection
def ReadFields(NodeValue: object) -> Mapping[str, object]:
    FieldData = getattr(NodeValue, "f", None)
    if not isinstance(FieldData, Mapping):
        raise TypeError("decoded archive node requires a field mapping")
    return CastValue(Mapping[str, object], FieldData)
