# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.adapters.Fusion.Native.Rectangle.CheckDimLayout import CheckDimLayout


# stale presentation extension points stay in source state while the measured carrier is checked
def CheckDimCache(
    Fields: dict[str, KEntityValue],
    Param: NativeNode,
    Points: tuple[tuple[float, float, float], ...],
    IsWidth: bool,
    YzDatum: bool = False,
    Fixed: bool = False,
) -> None:
    InfoValue = ObjectFields(Fields["LinearDimensionInfo"])
    Start, Finish = Points
    AxisValue = int(IsWidth) if YzDatum else int(not IsWidth)
    Amount = NumberValue(Param.Fields["value"])
    Other = Finish if IsWidth else Start
    SignedAmount = -Amount if YzDatum and not IsWidth else Amount
    SameNumbers(
        Other, (0.0, SignedAmount, 0.0) if AxisValue else (SignedAmount, 0.0, 0.0)
    )
    SameNumbers(
        (Distance(Start, Finish), NumberValue(InfoValue["length"])), (Amount, Amount)
    )
    SameNumbers(PointCoords(InfoValue["startPoint"]), Start)
    SameNumbers(PointCoords(InfoValue["endPoint"]), Finish)
    Plane = ObjectFields(InfoValue["plane"])
    Extension = PointCoords(InfoValue["extnStartPoint"])
    if (
        InfoValue["bDriven"] is not False
        or InfoValue["hasTextPoint"] is not True
        or InfoValue["isSingleArrow"] is not False
        or InfoValue["prefix"] != ("fx: " if Fixed else "")
        or InfoValue["text"] != Param.Fields["expression"]
        or Plane["normalReversed"] is not False
        or PointCoords(Plane["origin"]) != (0.0, 0.0, 0.0)
        or PointCoords(Plane["uAxis"]) != (1.0, 0.0, 0.0)
        or PointCoords(Plane["vAxis"]) != (0.0, 1.0, 0.0)
        or SeriesItems(Fields["RefPositions"]) != (0.0, 1.0)
        or Extension[1 - AxisValue] != 0.0
        or Extension[2] != 0.0
        or ((YzDatum or Fixed) and Extension != Start)
    ):
        raise ValueError(
            "Native rectangle dimension has inconsistent literal or annotation placement"
        )
    CheckDimLayout(InfoValue, Start, Finish, AxisValue)
