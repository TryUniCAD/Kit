# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping
from typing import Any as AnyValue

from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (
    KFieldOwners,
    KResolvedOps,
)


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, AnyValue] | None = None) -> bytes:
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
