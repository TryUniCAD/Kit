# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping as MappingBase
from dataclasses import fields as GetFields
from typing import cast as CastValue
from typing import get_origin as GetOrigin
from typing import get_type_hints as GetTypeHints

from interchange.serialization.RecordType import DataRecord


# repeated records share resolved mapping fields only while their owning decode operation remains active
def GetMapFieldsMut(
    TargetType: type[DataRecord],
    FieldCache: dict[type[DataRecord], tuple[str, ...]],
) -> tuple[str, ...]:
    FieldNames = FieldCache.get(TargetType)
    if FieldNames is None:
        TypeHints = CastValue(dict[str, object], GetTypeHints(TargetType))
        FieldNames = tuple(
            FieldValue.name
            for FieldValue in GetFields(TargetType)
            if GetOrigin(TypeHints.get(FieldValue.name)) is MappingBase
        )
        FieldCache[TargetType] = FieldNames
    return FieldNames
