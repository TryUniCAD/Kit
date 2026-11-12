from math import cos as Cosine, sin as SineOf

from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import KShapeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanHeading


def FaceSurface(FaceValue: KShapeFace) -> tuple[PlaneNode | ConeNode, bool]:
    Prefix = EntityPrefix(-1, -1)
    if not isinstance(FaceValue, WallFace):
        Normal = (0.0, 0.0, 1.0 if FaceValue.Upward else -1.0)
        Origin = (0.0, 0.0, FaceValue.LevelCm)
        return (
            PlaneNode(
                Prefix, Origin, Normal, (1.0, 0.0, 0.0), False, None, None, None, None
            ),
            False,
        )
    SpanValue = FaceValue.Span
    if isinstance(SpanValue, LineSpan):
        HeadX, HeadY = SpanHeading(SpanValue, False)
        Origin = (SpanValue.StartCm[0], SpanValue.StartCm[1], FaceValue.LowerCm)
        Plane = PlaneNode(
            Prefix,
            Origin,
            (HeadY, -HeadX, 0.0),
            (HeadX, HeadY, 0.0),
            False,
            None,
            None,
            None,
            None,
        )
        return Plane, False
    Middle = SpanValue.StartAngle + SpanValue.SweepAngle / 2.0
    Major = (
        SpanValue.RadiusCm * Cosine(Middle),
        SpanValue.RadiusCm * SineOf(Middle),
        0.0,
    )
    Origin = (SpanValue.CenterCm[0], SpanValue.CenterCm[1], FaceValue.LowerCm)
    Cylinder = ConeNode(
        Prefix,
        Origin,
        (0.0, 0.0, 1.0),
        Major,
        1.0,
        None,
        None,
        0.0,
        1.0,
        SpanValue.RadiusCm,
        False,
        None,
        None,
        None,
        None,
    )
    return Cylinder, SpanValue.SweepAngle < 0
