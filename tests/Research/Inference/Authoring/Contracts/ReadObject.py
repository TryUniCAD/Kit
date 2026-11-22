# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue


# research boundary records retain string keys before typed callers inspect nested data
def ReadObject(Value: object) -> dict[str, object]:
    if not isinstance(Value, dict):
        raise ValueError("expected a research record object")
    Record = CastValue(dict[object, object], Value)
    if not all(isinstance(KeyText, str) for KeyText in Record):
        raise ValueError("research record keys must be strings")
    return CastValue(dict[str, object], Record)
