from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceLabelOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace


def SketchCurve(
    BodyValue: ShapeBody, FaceValue: KShapeFace, EdgeValue: KShapeEdge
) -> int | None:
    if not isinstance(EdgeValue, LevelEdge):
        return None
    if EdgeValue.LevelCm != BodyValue.BaseLevelCm:
        return None
    Owner = FaceLabelOf(FaceValue).OperationIds
    if (
        not isinstance(FaceValue, WallFace)
        and Owner != EdgeValue.Span.Label.OperationIds
    ):
        return None
    Curves = dict(BodyValue.SketchCurves)
    return Curves.get(EdgeValue.Span.Label)
