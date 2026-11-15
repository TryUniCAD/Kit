from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace as ReplaceData
import math as MathValue
import re as RegexLib
import struct as Struct

from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    DEFINITION_STREAM as KDefinitionStream,
)
from convert.adapters.solidworks.drawing.Models import (
    DrawingSheet,
    DrawingView,
    ViewEdge,
    ViewOrientation,
)
from interchange import Vector3

# the scanner needs the direction width before it can reach the flag
KDirectionLength = 24

# the flag decides whether a matrix follows so the scanner must read it first
KFlagOffset = 24

# the matrix width lets the scanner skip it when the flag is set
KMatrixLength = 72

# the translation width keeps the trailing scale check aligned
KTranslationLength = 24

# the trailing scale confirms the record before it is trusted
KScaleLength = 8

# the longest record bounds the scan so the last record is not skipped
KRecordLength = KDirectionLength + 1 + KMatrixLength + KTranslationLength + KScaleLength

# binary noise rarely forms a unit vector so this tolerance rejects it
KUnitTolerance = 1e-06

# the centre match separates view records from other unit vector records
KCentreTolerance = 1e-06

# the creation index binds records because keyword order is not creation order
KViewIndex = RegexLib.compile(r"(\d+)$")


# noise rejection needs a unit check before any record is accepted
def IsUnit(Values: Sequence[float]) -> bool:
    return (
        abs(MathValue.sqrt(sum(ItemValue * ItemValue for ItemValue in Values)) - 1.0)
        < KUnitTolerance
    )


# a malformed matrix must be rejected before it can corrupt sheet edges
def IsRotation(Values: tuple[float, ...]) -> bool:
    MatrixRows = (Values[0:3], Values[3:6], Values[6:9])
    if any((not IsUnit(RowValue) for RowValue in MatrixRows)):
        return False
    for LeftIndex in range(3):
        for RightIndex in range(LeftIndex + 1, 3):
            if (
                abs(
                    sum(
                        MatrixRows[LeftIndex][Index] * MatrixRows[RightIndex][Index]
                        for Index in range(3)
                    )
                )
                > KUnitTolerance
            ):
                return False
    Determinant = (
        MatrixRows[0][0]
        * (MatrixRows[1][1] * MatrixRows[2][2] - MatrixRows[1][2] * MatrixRows[2][1])
        - MatrixRows[0][1]
        * (MatrixRows[1][0] * MatrixRows[2][2] - MatrixRows[1][2] * MatrixRows[2][0])
        + MatrixRows[0][2]
        * (MatrixRows[1][0] * MatrixRows[2][1] - MatrixRows[1][1] * MatrixRows[2][0])
    )
    return abs(Determinant - 1.0) < KUnitTolerance


# the centre match is the only reliable way to identify view records
def IsCentreMatch(
    Matrix: tuple[tuple[float, float, float], ...],
    Translation: tuple[float, float, float],
    Centre: Vector3,
) -> bool:
    Rotated = tuple(
        sum(
            Matrix[Column][RowIndex] * (Centre.x, Centre.y, Centre.z)[Column]
            for Column in range(3)
        )
        for RowIndex in range(3)
    )
    return all(
        (
            abs(Translation[Index] + Rotated[Index]) < KCentreTolerance
            for Index in range(3)
        )
    )


# only centre matched records are returned so unrelated vectors are ignored
def OrientRecords(DataValue: bytes, Centre: Vector3) -> tuple[ViewOrientation, ...]:
    Result: list[ViewOrientation] = []
    for Offset in range(0, len(DataValue) - KRecordLength + 1):
        Direction = Struct.unpack_from("<3d", DataValue, Offset)
        if not IsUnit(Direction):
            continue
        FlagValue = DataValue[Offset + KFlagOffset]
        if FlagValue not in (0, 1):
            continue
        Cursor = Offset + KFlagOffset + 1
        if FlagValue == 1:
            Values = Struct.unpack_from("<9d", DataValue, Cursor)
            if not IsRotation(Values):
                continue
            Matrix = (Values[0:3], Values[3:6], Values[6:9])
            Cursor += KMatrixLength
        else:
            Matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        Translation = Struct.unpack_from("<3d", DataValue, Cursor)
        if not all(
            (
                MathValue.isfinite(ItemValue) and abs(ItemValue) < 1.0
                for ItemValue in Translation
            )
        ):
            continue
        if (
            abs(
                Struct.unpack_from("<d", DataValue, Cursor + KTranslationLength)[0]
                - 1.0
            )
            > 1e-09
        ):
            continue
        if not IsCentreMatch(Matrix, Translation, Centre):
            continue
        Result.append(ViewOrientation(Matrix))
    return tuple(Result)


# the suffix is needed because keyword order does not follow creation order
def ViewIndex(ViewName: str) -> int:
    Match = KViewIndex.search(ViewName)
    if Match is None:
        raise SldprtFormatError("drawing view name has no creation index")
    return int(Match.group(1))


# callers need sheet space segments because model space edges cannot be drawn
def SheetEdges(
    ViewValue: DrawingView, Orientation: ViewOrientation
) -> tuple[ViewEdge, ...]:
    Bounds = ViewValue.ModelBounds
    if (
        Bounds is None
        or ViewValue.PositionX is None
        or ViewValue.PositionY is None
        or ViewValue.ViewScale is None
    ):
        raise SldprtFormatError("drawing view is missing placement data")
    Matrix = Orientation.Matrix
    Centre = (Bounds.Center.x, Bounds.Center.y, Bounds.Center.z)
    PositionX = ViewValue.PositionX
    PositionY = ViewValue.PositionY
    Scale = ViewValue.ViewScale

    def Project(Point: Vector3) -> Vector3:
        Local = (Point.x - Centre[0], Point.y - Centre[1], Point.z - Centre[2])
        Rotated = tuple(
            sum(Matrix[Column][RowIndex] * Local[Column] for Column in range(3))
            for RowIndex in range(3)
        )
        return Vector3(
            PositionX + Scale * Rotated[0],
            PositionY + Scale * Rotated[1],
            0.0,
        )

    return tuple(
        ViewEdge(Project(EdgeValue.Start), Project(EdgeValue.End))
        for EdgeValue in ViewValue.Edges
    )


# a missing or extra record must fail closed rather than guess a rotation
def OrientSheets(
    Sheets: tuple[DrawingSheet, ...], Archive: SldprtArchive
) -> tuple[DrawingSheet, ...]:
    DataValue = Archive.get(KDefinitionStream)
    if DataValue is None:
        raise SldprtFormatError(f"drawing is missing {KDefinitionStream}")
    Views = tuple(ViewValue for SheetValue in Sheets for ViewValue in SheetValue.Views)
    if not Views:
        raise SldprtFormatError("drawing has no views")
    Centres = {
        ViewValue.ModelBounds.Center
        for ViewValue in Views
        if ViewValue.ModelBounds is not None
    }
    if len(Centres) != 1:
        raise SldprtFormatError("drawing views do not share one model centre")
    Centre = next(iter(Centres))
    Records = OrientRecords(DataValue, Centre)
    if len(Records) != len(Views):
        raise SldprtFormatError(
            "drawing orientation records do not match the view count"
        )
    Ordered = sorted(Views, key=lambda ViewValue: ViewIndex(ViewValue.Name))
    Bound = {ViewValue.Name: Records[Index] for Index, ViewValue in enumerate(Ordered)}
    NewSheets: list[DrawingSheet] = []
    for SheetValue in Sheets:
        NewViews: list[DrawingView] = []
        for ViewValue in SheetValue.Views:
            Orientation = Bound[ViewValue.Name]
            NewViews.append(
                ReplaceData(
                    ViewValue,
                    Orientation=Orientation,
                    SheetEdges=SheetEdges(ViewValue, Orientation),
                )
            )
        NewSheets.append(ReplaceData(SheetValue, Views=tuple(NewViews)))
    return tuple(NewSheets)
