# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# saved captions can move along the dimension line without changing the anchored geometry
def CheckDimLayout(
    InfoValue: dict[str, KEntityValue],
    Start: tuple[float, float, float],
    Finish: tuple[float, float, float],
    AxisValue: int,
    FixedCorner: bool,
) -> None:
    First = PointCoords(InfoValue["DimStartPoint"])
    Second = PointCoords(InfoValue["DimEndPoint"])
    Caption = PointCoords(InfoValue["textPosition"])
    SideAxis = 1 - AxisValue
    SameNumbers(
        (First[AxisValue], Second[AxisValue]), (Start[AxisValue], Finish[AxisValue])
    )
    SameNumbers(
        (First[2], Second[2], Caption[2], Second[SideAxis], Caption[SideAxis]),
        (0.0, 0.0, 0.0, First[SideAxis], First[SideAxis]),
    )
    if not FixedCorner:
        SameNumbers(
            (Caption[AxisValue],), ((Start[AxisValue] + Finish[AxisValue]) / 2,)
        )
