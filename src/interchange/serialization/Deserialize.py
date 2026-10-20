# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import base64 as BaseCodec
from enum import Enum as EnumBase

from interchange.serialization.DecodeRecord import DecodeRecord
from interchange.serialization.TypeRegistry import KTypeRegistry
from typing import Any as AnyValue


# recursive decoding validates registered types before constructing immutable model records
def FromData(SourceValue: AnyValue) -> AnyValue:
    if isinstance(SourceValue, list):
        return [FromData(ItemValue) for ItemValue in SourceValue]
    if not isinstance(SourceValue, dict):
        return SourceValue
    if set(SourceValue) == {"$bytes"}:
        return BaseCodec.b64decode(SourceValue["$bytes"], validate=True)
    if set(SourceValue) == {"$tuple"}:
        return tuple(FromData(ItemValue) for ItemValue in SourceValue["$tuple"])
    if set(SourceValue) == {"$frozenset"}:
        return frozenset(FromData(ItemValue) for ItemValue in SourceValue["$frozenset"])
    if set(SourceValue) == {"$set"}:
        return set(FromData(ItemValue) for ItemValue in SourceValue["$set"])
    if "$enum" in SourceValue:
        EnumType = KTypeRegistry.get(SourceValue["$enum"])
        if EnumType is None or not issubclass(EnumType, EnumBase):
            raise ValueError(f"unknown enum type {SourceValue['$enum']!r}")
        return EnumType(SourceValue["value"])
    WireType = SourceValue.get("$type")
    if not WireType:
        return {
            KeyValue: FromData(ItemValue) for KeyValue, ItemValue in SourceValue.items()
        }
    TargetType = KTypeRegistry.get(WireType)
    if TargetType is None:
        raise ValueError(f"unknown data type {WireType!r}")
    return DecodeRecord(SourceValue, TargetType, FromData)
