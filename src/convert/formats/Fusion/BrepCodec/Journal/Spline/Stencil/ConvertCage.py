from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
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
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilKey import (
    StencilKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilRows import (
    Cartesian,
    EvaluateRows,
    PickPoint,
    StencilRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface

KRationalForm = "both"


def IsRational(Values: StencilRows, Indices: tuple[int, ...]) -> bool:
    return any(Values.Weighted[Index] for Index in Indices)


def MakeFace(FaceValue: StencilFace, Values: StencilRows) -> FaceResult:
    Indices = FaceValue.Poles
    if IsRational(Values, Indices):
        Masses = tuple(Values.Homogeneous[Index] for Index in Indices)
        Points = tuple(Cartesian(MassValue) for MassValue in Masses)
        Weights = tuple(MassValue[3] for MassValue in Masses)
        Result = NubsSurface(
            3,
            3,
            0,
            0,
            0,
            0,
            FaceValue.KnotsU,
            FaceValue.KnotsV,
            Points,
            Weights,
            KRationalForm,
        )
    else:
        Points = tuple(Values.Points[Index] for Index in Indices)
        Result = NubsSurface(
            3, 3, 0, 0, 0, 0, FaceValue.KnotsU, FaceValue.KnotsV, Points
        )
    return FaceResult(FaceValue.FaceIndex, Result, SurfaceOrders(Result))


def MakeCurve(CurveValue: StencilCurve, Values: StencilRows) -> BsCurve:
    Indices = CurveValue.Poles
    Knots, Counts = CurveValue.Knots, CurveValue.Multiplicity
    if IsRational(Values, Indices):
        Masses = tuple(Values.Homogeneous[Index] for Index in Indices)
        Poles = tuple(Cartesian(MassValue) for MassValue in Masses)
        Weights = tuple(MassValue[3] for MassValue in Masses)
        return BsCurve(True, 3, 0, Knots, Counts, 3, Poles, Weights)
    Poles = tuple(Values.Points[Index] for Index in Indices)
    return BsCurve(False, 3, 0, Knots, Counts, 3, Poles, ())


def ApplyStencil(Table: StencilTable, Surface: TsplineSurface) -> CageResult:
    if len(Surface.Grips) != Table.GripCount:
        raise ValueError("Fusion Form stencil needs the table grip count")
    Values = EvaluateRows(Table.Rows, Surface.Grips)
    Faces = tuple(MakeFace(FaceValue, Values) for FaceValue in Table.Faces)
    Curves = tuple(MakeCurve(CurveValue, Values) for CurveValue in Table.Curves)
    return CageResult(
        Table.LayoutKey,
        Faces,
        Curves,
        tuple(CurveOrders(Curve) for Curve in Curves),
        tuple(PickPoint(Values, Index) for Index in Table.Points),
    )


def ConvertCage(Surface: TsplineSurface) -> CageResult:
    CheckSurface(Surface)
    if any(EdgeValue.KnotInterval != 1.0 for EdgeValue in Surface.Topology.Edges):
        raise ValueError("Fusion Form stencil conversion needs unit knot intervals")
    Table = ReadStencils().get(StencilKey(Surface))
    if Table is None:
        raise ValueError("Fusion Form conversion has no stencil for this cage layout")
    return ApplyStencil(Table, Surface)
