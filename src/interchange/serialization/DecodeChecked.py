# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange.serialization.DecodeRecord import DecodeRecordMut
from interchange.serialization.DecodeTagged import DecodeTagged
from interchange.serialization.DecodeTagged import KTagNames
from interchange.serialization.GetEnumType import GetEnumType
from interchange.serialization.GetRecordType import GetRecordType
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.WireData import KWireData


# the root check already covers every nested value so recursion must not walk each subtree again
def DecodeChecked(
    DataValue: KWireData,
    FieldCache: dict[type[DataRecord], tuple[str, ...]],
) -> object:
    if isinstance(DataValue, list):
        return [DecodeChecked(ItemValue, FieldCache) for ItemValue in DataValue]
    if not isinstance(DataValue, dict):
        return DataValue
    if len(DataValue) == 1 and next(iter(DataValue)) in KTagNames:
        TagName = next(iter(DataValue))
        TagValue = DataValue[TagName]
        if TagName == "$bytes":
            return DecodeTagged(TagName, TagValue)
        if not isinstance(TagValue, list):
            raise ValueError(f"{TagName} value must be a list")
        return DecodeTagged(
            TagName, [DecodeChecked(ItemValue, FieldCache) for ItemValue in TagValue]
        )
    if "$enum" in DataValue:
        EnumType = GetEnumType(DataValue)
        return EnumType(DecodeChecked(DataValue["value"], FieldCache))
    if "$type" not in DataValue:
        return {
            KeyValue: DecodeChecked(ItemValue, FieldCache)
            for KeyValue, ItemValue in DataValue.items()
        }
    return DecodeRecordMut(
        DataValue, GetRecordType(DataValue), DecodeChecked, FieldCache
    )
