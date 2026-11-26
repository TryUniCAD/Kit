from base64 import b64encode as EncodeBase
from collections.abc import Hashable, Mapping
from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
from functools import lru_cache as CacheValues
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.Fusion.State.StateTypes import KStateTypes

# fixed supported classes need constant time membership checks during recursive encoding
KEncodeTypes = frozenset(KStateTypes)


# registered classes reuse their declared field order throughout the same process
@CacheValues(maxsize=len(KEncodeTypes))
def GetStateFields(ValueType: type[object]) -> tuple[str, ...]:
    if not IsDataClass(ValueType):
        raise TypeError("Fusion semantic-state records must be dataclasses")
    return tuple(Field.name for Field in DataFields(ValueType))


# the state operation needs a consistent construction rule so public document claims remain grounded in native records
def EncodeState(Value: object, Depth: int = 0) -> object:
    if Depth > 64:
        raise ValueError("Fusion semantic state exceeds nesting limit")
    ValueType = type(Value)
    if Value is None or ValueType in (str, int, bool):
        return Value
    if type(Value) is float and IsFinite(Value):
        return Value
    if ValueType in KEncodeTypes:
        ClassName = f"{ValueType.__module__}.{ValueType.__name__}"
        if isinstance(Value, EnumBase):
            return {"enum": ClassName, "value": Value.value}
        if IsDataClass(Value) and not isinstance(Value, type):
            return {
                "record": ClassName,
                "fields": {
                    FieldName: EncodeState(getattr(Value, FieldName), Depth + 1)
                    for FieldName in GetStateFields(CastValue(Hashable, ValueType))
                },
            }
    if isinstance(Value, bytes) and len(Value) <= 2000000:
        return {"bytes": EncodeBase(Value).decode("ascii")}
    if isinstance(Value, tuple):
        return {
            "tuple": [
                EncodeState(ItemValue, Depth + 1)
                for ItemValue in CastValue(tuple[object, ...], Value)
            ]
        }
    if isinstance(Value, Mapping) and all(
        isinstance(FieldKey, str)
        for FieldKey in CastValue(Mapping[object, object], Value)
    ):
        return {
            "map": {
                FieldKey: EncodeState(ItemValue, Depth + 1)
                for FieldKey, ItemValue in CastValue(
                    Mapping[str, object], Value
                ).items()
            }
        }
    raise ValueError("Unsupported Fusion semantic-state value")
