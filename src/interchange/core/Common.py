# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from types import MappingProxyType as FrozenMap
from typing import Any as AnyValue
from typing import Mapping as TypeMap


# recursive scalar typing exists because payload contracts must reject unsupported primitive values
KJsonScalar = str | int | float | bool | None


# recursive container typing exists because adapters retain nested native metadata losslessly
KJsonValue = KJsonScalar | list["KJsonValue"] | dict[str, "KJsonValue"]


# immutable mappings prevent accidental mutation of frozen interchange records
def FreezeMapping(
    SourceValues: TypeMap[str, AnyValue] | None = None,
) -> TypeMap[str, AnyValue]:
    return FrozenMap(dict(SourceValues or {}))
