from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFolds import (
    CheckFolds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ClassifyEdges import (
    ClassifyEdges,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import (
    ConvertCage,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadShapes import (
    ReadShapes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilShape import (
    StencilShape,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def ShapeEdges(Shape: StencilShape, Result: CageResult) -> tuple[FormEdge, ...]:
    return tuple(
        FormEdge(
            EdgeValue.StartVertex,
            EdgeValue.EndVertex,
            Result.Curves[EdgeValue.CurveIndex],
            Result.CurveJumps[EdgeValue.CurveIndex],
            EdgeValue.Convexity,
            EdgeValue.Label,
            EdgeValue.Windows,
            EdgeValue.Bounds,
        )
        for EdgeValue in Shape.Edges
    )


def ShapeFaces(Shape: StencilShape, Result: CageResult) -> tuple[FormFace, ...]:
    Found = {FaceValue.FaceIndex: FaceValue for FaceValue in Result.Faces}
    return tuple(
        FormFace(
            FormSurface(
                Found[FaceValue.FaceIndex].Surface,
                Found[FaceValue.FaceIndex].Jumps,
                FaceValue.FaceIndex,
            ),
            FaceValue.Uses,
            FaceValue.Label,
            FaceValue.DoubleSided,
            FaceValue.Contained,
        )
        for FaceValue in Shape.Faces
    )


def ShapeBody(Surface: TsplineSurface) -> FormBody:
    Result = ConvertCage(Surface)
    Shape = ReadShapes().get(Result.LayoutKey)
    if Shape is None:
        raise ValueError("Fusion Form conversion has no body shape for this layout")
    return FormBody(
        tuple(Result.Points[Index] for Index in Shape.Points),
        ShapeEdges(Shape, Result),
        ShapeFaces(Shape, Result),
        Shape.Regions,
    )


def CageBody(Surface: TsplineSurface) -> FormBody:
    BodyValue = ClassifyEdges(ShapeBody(Surface))
    CheckFolds(BodyValue)
    return BodyValue
