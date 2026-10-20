# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping
from typing import Any as AnyValue


# feature identity exposes unsupported grammar without relying on unstable source filenames
def FeatureTypes(DocumentData: AnyValue) -> tuple[str, ...]:
    TypeNames: set[str] = set()
    for FeatureData in DocumentData.feature_timeline:
        FreecadData = FeatureData.attributes.get("freecad")
        TypeName = (
            FreecadData.get("type_id", "") if isinstance(FreecadData, Mapping) else ""
        )
        TypeNames.add(str(TypeName or FeatureData.kind))
    return tuple(sorted(TypeNames))
