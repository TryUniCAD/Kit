from __future__ import annotations

import base64 as BaseCodec
from collections.abc import Mapping as MappingBase
from collections.abc import Set as SetBase
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
import json as JsonCodec
from typing import cast as CastValue

from interchange.serialization.OptionalFields import KOmitNullField
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.Wire import GetWireField, GetWireType
from interchange.serialization.WireData import KWireData


# unordered collections need canonical ordering so output remains stable across hash seeds
def OrderData(SourceValues: SetBase[object]) -> list[KWireData]:
    EncodedValues = [ToData(ItemValue) for ItemValue in SourceValues]

    # canonical text ordering avoids dependence on collection hash iteration order
    def GetSortKey(ItemValue: KWireData) -> str:
        return JsonCodec.dumps(
            ItemValue, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    return sorted(EncodedValues, key=GetSortKey)


# absent additive properties must leave earlier document encodings identical
def EncodeRecord(SourceValue: DataRecord) -> dict[str, KWireData]:
    ValueType = type(SourceValue)
    ResultValue: dict[str, KWireData] = {"$type": GetWireType(ValueType)}
    for FieldValue in GetFields(SourceValue):
        MemberValue = CastValue(object, getattr(SourceValue, FieldValue.name))
        if MemberValue is None and FieldValue.metadata.get(KOmitNullField):
            continue
        ResultValue[GetWireField(FieldValue.name, ValueType)] = ToData(MemberValue)
    return ResultValue


# recursive encoding preserves every supported container and model type losslessly
def ToData(SourceValue: object) -> KWireData:
    if IsDataClass(SourceValue) and not isinstance(SourceValue, type):
        return EncodeRecord(SourceValue)
    if isinstance(SourceValue, EnumBase):
        return {
            "$enum": GetWireType(type(SourceValue)),
            "value": ToData(CastValue(object, SourceValue.value)),
        }
    if isinstance(SourceValue, bytes):
        return {"$bytes": BaseCodec.b64encode(SourceValue).decode("ascii")}
    if isinstance(SourceValue, tuple):
        TupleValue = CastValue(tuple[object, ...], SourceValue)
        return {"$tuple": [ToData(ItemValue) for ItemValue in TupleValue]}
    if isinstance(SourceValue, frozenset):
        FrozenValues = CastValue(frozenset[object], SourceValue)
        return {"$frozenset": OrderData(FrozenValues)}
    if isinstance(SourceValue, set):
        MutableValues = CastValue(set[object], SourceValue)
        return {"$set": OrderData(MutableValues)}
    if isinstance(SourceValue, list):
        ListValue = CastValue(list[object], SourceValue)
        return [ToData(ItemValue) for ItemValue in ListValue]
    if isinstance(SourceValue, MappingBase):
        MapValue = CastValue(MappingBase[object, object], SourceValue)
        ResultValue: dict[str, KWireData] = {}
        for KeyValue, ItemValue in MapValue.items():
            if not isinstance(KeyValue, str):
                raise TypeError("wire object keys must be strings")
            ResultValue[KeyValue] = ToData(ItemValue)
        return ResultValue
    if SourceValue is None or isinstance(SourceValue, (str, int, float, bool)):
        return SourceValue
    raise TypeError(f"cannot serialize value of type {type(SourceValue).__name__}")
