# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue
from typing import Mapping as TypeMap


# migrations can revise type metadata while older records in the same decode already cached it
def BindMapHintMut(
    RecordType: type[object], FieldValues: TypeMap[str, object]
) -> TypeMap[str, object]:
    MetaValue = FieldValues["Metadata"]
    if not isinstance(MetaValue, dict):
        raise TypeError("migration metadata must remain a dictionary")
    MappingValue = CastValue(dict[str, object], MetaValue)
    RecordType.__annotations__["Metadata"] = (
        dict[str, object] if MappingValue.get("mutable") else TypeMap[str, object]
    )
    return FieldValues
