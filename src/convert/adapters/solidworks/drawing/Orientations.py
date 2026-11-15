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

# the orientation record starts with a unit view direction
KDirectionLength = 24

# a one byte flag follows the direction and selects the optional matrix
KFlagOffset = 24

# a stored matrix is nine row major doubles
KMatrixLength = 72

# the translation follows the matrix or the flag
KTranslationLength = 24

# the record ends with a unit scale double
KScaleLength = 8

# a unit vector is accepted within this tolerance
KUnitTolerance = 1e-06

# the record translation must match the negated rotated centre within this tolerance
KCentreTolerance = 1e-06

# the view name carries its creation index as a trailing integer
KViewIndex = RegexLib.compile(r"(\d+)$")


# a unit vector is required before a record can be considered an orientation
def IsUnit(Values: Sequence[float]) -> bool:
    return (
        abs(MathValue.sqrt(sum(ItemValue * ItemValue for ItemValue in Values)) - 1.0)
        < KUnitTolerance
    )


# a stored matrix must be a proper rotation before it can be trusted
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


# the record translation is the negated rotated model centre
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


# orientation records are recovered only when the translation matches the model centre
def OrientRecords(DataValue: bytes, Centre: Vector3) -> tuple[ViewOrientation, ...]:
    Result: list[ViewOrientation] = []
    for Offset in range(0, len(DataValue) - 200):
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


# the view name suffix is the creation index used to bind orientation records
def ViewIndex(ViewName: str) -> int:
    Match = KViewIndex.search(ViewName)
    if Match is None:
        raise SldprtFormatError("drawing view name has no creation index")
    return int(Match.group(1))


# sheet space edges are the model edges rotated into the view frame and scaled
def SheetEdges(
    ViewValue: DrawingView, Orientation: ViewOrientation, Scale: float
) -> tuple[ViewEdge, ...]:
    Bounds = ViewValue.ModelBounds
    if Bounds is None or ViewValue.PositionX is None or ViewValue.PositionY is None:
        raise SldprtFormatError("drawing view is missing placement data")
    Matrix = Orientation.Matrix
    Centre = (Bounds.Center.x, Bounds.Center.y, Bounds.Center.z)
    PositionX = ViewValue.PositionX
    PositionY = ViewValue.PositionY

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


# orientation recovery needs the definition stream and one record per view
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
        Scale = SheetValue.ScaleNumerator / SheetValue.ScaleDenominator
        NewViews: list[DrawingView] = []
        for ViewValue in SheetValue.Views:
            Orientation = Bound[ViewValue.Name]
            NewViews.append(
                ReplaceData(
                    ViewValue,
                    Orientation=Orientation,
                    SheetEdges=SheetEdges(ViewValue, Orientation, Scale),
                )
            )
        NewSheets.append(ReplaceData(SheetValue, Views=tuple(NewViews)))
    return tuple(NewSheets)
