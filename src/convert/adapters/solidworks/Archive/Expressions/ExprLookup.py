from collections.abc import Callable, Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# expression lookups must retain inherited scope and computed count overrides
def ExprLookup(
    Arguments: tuple[object, ...],
    ReadValue: Callable[[tuple[object, ...]], object],
    IsDefault: bool,
) -> object:
    OwnerValue = ReadValue(CastValue(tuple[object, ...], Arguments[0]))
    KeyValue = ReadValue(CastValue(tuple[object, ...], Arguments[1]))
    try:
        if isinstance(OwnerValue, FieldScope):
            return ReadScopeValue(OwnerValue, CastValue(str, KeyValue))
        if isinstance(OwnerValue, Mapping):
            return CastValue(Mapping[object, object], OwnerValue)[KeyValue]
        if isinstance(OwnerValue, Sequence):
            return CastValue(Sequence[object], OwnerValue)[CastValue(int, KeyValue)]
        raise ValueError("native expression lookup has no typed field owner")
    except KeyError:
        if not IsDefault:
            raise
        return ReadValue(CastValue(tuple[object, ...], Arguments[2]))
