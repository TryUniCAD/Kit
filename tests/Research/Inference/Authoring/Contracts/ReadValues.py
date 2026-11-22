# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue


# serialized research rosters must remain arrays before a typed caller iterates them
def ReadValues(Value: object) -> list[object]:
    if not isinstance(Value, list):
        raise ValueError("expected a research record array")
    return CastValue(list[object], Value)
