# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue


# solver equivalence alone cannot qualify changed operand order in the emitted archive
def CheckOperandMap(OperandOrder: object) -> None:
    RowsValue = CastValue(dict[str, dict[str, object]], OperandOrder)
    assert set(RowsValue) == {"width_mm", "height_mm"}
    Origin = [0.0, 0.0, 0.0]
    WidthEnd = [40.0, 0.0, 0.0]
    HeightEnd = [0.0, 20.0, 0.0]
    assert RowsValue["width_mm"] == {
        "source_world_mm": [Origin, WidthEnd],
        "target_world_mm": [Origin, WidthEnd],
        "status": "preserved",
    }
    assert RowsValue["height_mm"] == {
        "source_world_mm": [Origin, HeightEnd],
        "target_world_mm": [HeightEnd, Origin],
        "status": "reversed_unqualified",
    }
