# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64 as BaseCodec

from interchange.serialization.DecodeRecord import DecodeRecordMut
from interchange.serialization.GetEnumType import GetEnumType
from interchange.serialization.GetRecordType import GetRecordType
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.WireData import CheckWireData


# recursive decoding validates registered types before constructing immutable model records
def DecodeValue(
    SourceValue: object,
    FieldCache: dict[type[DataRecord], tuple[str, ...]],
) -> object:
    DataValue = CheckWireData(SourceValue)
    if isinstance(DataValue, list):
        return [DecodeValue(ItemValue, FieldCache) for ItemValue in DataValue]
    if not isinstance(DataValue, dict):
        return DataValue
    KeyValues = set(DataValue)
    if KeyValues == {"$bytes"}:
        EncodedValue = DataValue["$bytes"]
        if not isinstance(EncodedValue, str):
            raise ValueError("encoded bytes must be text")
        return BaseCodec.b64decode(EncodedValue, validate=True)
    if KeyValues in ({"$tuple"}, {"$frozenset"}, {"$set"}):
        TagName = next(iter(KeyValues))
        ItemValues = DataValue[TagName]
        if not isinstance(ItemValues, list):
            raise ValueError(f"{TagName} value must be a list")
        DecodedValues = [DecodeValue(ItemValue, FieldCache) for ItemValue in ItemValues]
        if TagName == "$tuple":
            return tuple(DecodedValues)
        if TagName == "$frozenset":
            return frozenset(DecodedValues)
        return set(DecodedValues)
    if "$enum" in DataValue:
        EnumType = GetEnumType(DataValue)
        return EnumType(DecodeValue(DataValue["value"], FieldCache))
    if "$type" not in DataValue:
        return {
            KeyValue: DecodeValue(ItemValue, FieldCache)
            for KeyValue, ItemValue in DataValue.items()
        }
    return DecodeRecordMut(
        DataValue,
        GetRecordType(DataValue),
        DecodeValue,
        FieldCache,
    )
