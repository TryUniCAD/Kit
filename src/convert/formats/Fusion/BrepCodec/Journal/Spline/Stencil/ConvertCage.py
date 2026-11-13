from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    CurveOrders,
    SurfaceOrders,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.FaceResult import (
    FaceResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadStencils import (
    ReadStencils,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilKey import (
    StencilKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def RowPoint(
    RowValue: tuple[tuple[int, float], ...], Grips: tuple[ControlGrip, ...]
) -> KJournalVector:
    return (
        sum(Value * Grips[Index].CoordX for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordY for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordZ for Index, Value in RowValue),
    )


def ApplyStencil(Table: StencilTable, Surface: TsplineSurface) -> CageResult:
    if len(Surface.Grips) != Table.GripCount:
        raise ValueError("Fusion Form stencil needs the table grip count")
    Values = tuple(RowPoint(RowValue, Surface.Grips) for RowValue in Table.Rows)
    Faces: list[FaceResult] = []
    for FaceValue in Table.Faces:
        Points = tuple(Values[Index] for Index in FaceValue.Poles)
        Result = NubsSurface(
            3, 3, 0, 0, 0, 0, FaceValue.KnotsU, FaceValue.KnotsV, Points
        )
        Faces.append(FaceResult(FaceValue.FaceIndex, Result, SurfaceOrders(Result)))
    Curves = tuple(
        BsCurve(
            False,
            3,
            0,
            CurveValue.Knots,
            CurveValue.Multiplicity,
            3,
            tuple(Values[Index] for Index in CurveValue.Poles),
            (),
        )
        for CurveValue in Table.Curves
    )
    return CageResult(
        Table.LayoutKey,
        tuple(Faces),
        Curves,
        tuple(CurveOrders(Curve) for Curve in Curves),
        tuple(Values[Index] for Index in Table.Points),
    )


def ConvertCage(Surface: TsplineSurface) -> CageResult:
    CheckSurface(Surface)
    Table = ReadStencils().get(StencilKey(Surface))
    if Table is None:
        raise ValueError("Fusion Form conversion has no stencil for this cage layout")
    return ApplyStencil(Table, Surface)
