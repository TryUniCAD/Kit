# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue


# json object validation keeps process boundary records typed without trusting decoder annotations
def ReadRecord(Value: object) -> dict[str, object]:
    assert isinstance(Value, dict)
    Record = CastValue(dict[object, object], Value)
    assert all(isinstance(FieldName, str) for FieldName in Record)
    return CastValue(dict[str, object], Record)
