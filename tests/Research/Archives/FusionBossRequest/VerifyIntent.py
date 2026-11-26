# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import cast as CastValue


# source relation custody must retain the saved order before target canonicalization
def VerifyIntent(Witness: dict[str, object]) -> None:
    Source = CastValue(dict[str, object], Witness["source_evidence"])
    RowsValue = CastValue(list[list[object]], Witness["source_ordered_relations"])
    assert Source["source_sha256"] == (
        "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"
    )
    assert Source["source_operation"] == "join"
    assert [RowValue[1] for RowValue in RowsValue] == [
        "horizontal",
        "vertical",
        "horizontal",
        "vertical",
        "distance",
        "distance",
        "coincident",
    ]
    assert "height_mm" in str(RowsValue[4][0])
    assert "width_mm" in str(RowsValue[5][0])
    HeightRefs = CastValue(list[list[object]], RowsValue[4][2])
    FirstEdge, LastEdge = RowsValue[0][2], RowsValue[3][2]
    (WidthLine,) = CastValue(list[list[object]], FirstEdge)
    (HeightLine,) = CastValue(list[list[object]], LastEdge)
    assert HeightRefs == [[HeightLine[0], "end"], [HeightLine[0], "start"]]
    assert RowsValue[-1][2] == [[Source["origin"], ""], [WidthLine[0], "start"]]
