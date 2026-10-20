# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import base64 as BaseCodec
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
import json as JsonCodec
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.serialization.Wire import GetWireField, GetWireType


# unordered collections need canonical ordering so output remains stable across hash seeds
def OrderData(SourceValues: set[AnyValue] | frozenset[AnyValue]) -> list[AnyValue]:
    EncodedValues = [ToData(ItemValue) for ItemValue in SourceValues]

    # canonical text ordering avoids dependence on collection hash iteration order
    def GetSortKey(ItemValue: AnyValue) -> str:
        return JsonCodec.dumps(
            ItemValue, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    return sorted(EncodedValues, key=GetSortKey)


# recursive encoding preserves every supported container and model type losslessly
def ToData(SourceValue: AnyValue) -> AnyValue:
    if IsDataClass(SourceValue):
        ResultValue = {"$type": GetWireType(type(SourceValue))}
        for FieldValue in GetFields(SourceValue):
            ResultValue[GetWireField(FieldValue.name, type(SourceValue))] = ToData(
                getattr(SourceValue, FieldValue.name)
            )
        return ResultValue
    if isinstance(SourceValue, EnumBase):
        return {"$enum": GetWireType(type(SourceValue)), "value": SourceValue.value}
    if isinstance(SourceValue, bytes):
        return {"$bytes": BaseCodec.b64encode(SourceValue).decode("ascii")}
    if isinstance(SourceValue, tuple):
        return {"$tuple": [ToData(ItemValue) for ItemValue in SourceValue]}
    if isinstance(SourceValue, frozenset):
        return {"$frozenset": OrderData(SourceValue)}
    if isinstance(SourceValue, set):
        return {"$set": OrderData(SourceValue)}
    if isinstance(SourceValue, list):
        return [ToData(ItemValue) for ItemValue in SourceValue]
    if isinstance(SourceValue, TypeMap):
        return {
            str(KeyValue): ToData(ItemValue)
            for KeyValue, ItemValue in SourceValue.items()
        }
    if SourceValue is None or isinstance(SourceValue, (str, int, float, bool)):
        return SourceValue
    raise TypeError(f"cannot serialize value of type {type(SourceValue).__name__}")
