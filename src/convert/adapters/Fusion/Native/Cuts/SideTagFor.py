from math import isclose as IsClose
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from interchange.geometry.Models.VectorPlane import PlaneVector


# a split final side retains the tag of the unique original profile edge containing it
def SideTagFor(
    First: PlaneVector,
    Second: PlaneVector,
    Shapes: tuple[RectGeometry, RectGeometry],
    Labels: tuple[dict[int, FeatureTag], dict[int, FeatureTag]],
) -> FeatureTag:
    Matches: list[FeatureTag] = []
    for Shape, TagMap in zip(Shapes, Labels, strict=True):
        for LineNode, LineValue in zip(Shape.LineNodes, Shape.Lines, strict=True):
            if all(
                all(
                    min(Start, Finish) - 1e-8 <= Amount <= max(Start, Finish) + 1e-8
                    for Amount, Start, Finish in (
                        (Point.x, LineValue.start.x, LineValue.end.x),
                        (Point.y, LineValue.start.y, LineValue.end.y),
                    )
                )
                and IsClose(
                    (LineValue.end.x - LineValue.start.x)
                    * (Point.y - LineValue.start.y)
                    - (LineValue.end.y - LineValue.start.y)
                    * (Point.x - LineValue.start.x),
                    0.0,
                    abs_tol=1e-7,
                )
                for Point in (First, Second)
            ):
                Matches.append(TagMap[CurveTag(LineNode)])
    if len(Matches) != 1:
        raise ValueError("Native cut side does not identify a unique authored edge")
    return Matches[0]
