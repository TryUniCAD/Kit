# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from enum import Enum as EnumBase

from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.WireData import KWireData


# enum resolution must finish before child decoding to preserve supported recursion depth
def GetEnumType(DataValue: dict[str, KWireData]) -> type[EnumBase]:
    if set(DataValue) != {"$enum", "value"}:
        raise ValueError("encoded enum must contain only type and value")
    EnumName = DataValue["$enum"]
    if not isinstance(EnumName, str) or not EnumName:
        raise ValueError("encoded enum type must be nonempty text")
    EnumType = KTypeRegistry.get(EnumName)
    if EnumType is None or not issubclass(EnumType, EnumBase):
        raise ValueError(f"unknown enum type {EnumName!r}")
    return EnumType
