from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan


def SketchCurve(BodyValue: ShapeBody, EdgeValue: KShapeEdge) -> int | None:
    if not isinstance(EdgeValue, LevelEdge) or not isinstance(EdgeValue.Span, LineSpan):
        return None
    if (
        EdgeValue.LevelCm != BodyValue.BaseLevelCm
        or len(EdgeValue.Span.Label.OperationIds) != 1
    ):
        return None
    Curves = dict(BodyValue.SketchCurves)
    return Curves.get(EdgeValue.Span.Label.PrimaryId)
