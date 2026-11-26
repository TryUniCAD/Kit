from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# computed count prefixes need the actual ordered rows without copying lazy model providers
def ReadBodyRows(ScopeValue: FieldScope, FieldName: str) -> Sequence[object]:
    Value = ReadScopeValue(ScopeValue, FieldName)
    if not isinstance(Value, Sequence) or isinstance(Value, (str, bytes, bytearray)):
        raise ValueError(f"native body field {FieldName} requires ordered rows")
    return CastValue(Sequence[object], Value)
