from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import KShapeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


def FaceKey(FaceValue: KShapeFace) -> tuple[object, ...]:
    if isinstance(FaceValue, WallFace):
        return ("wall", FaceValue.Span, FaceValue.LowerCm, FaceValue.UpperCm)
    return (
        "cap",
        FaceValue.LevelCm,
        FaceValue.Upward,
        FaceValue.Label,
        FaceValue.Loops[0][0].Edge,
    )


def FaceLabelOf(FaceValue: KShapeFace) -> FaceLabel:
    return FaceValue.Span.Label if isinstance(FaceValue, WallFace) else FaceValue.Label
