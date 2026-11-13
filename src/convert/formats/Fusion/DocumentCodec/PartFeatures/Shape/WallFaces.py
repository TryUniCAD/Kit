from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RiseEdge import RiseEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
    SpanFinish,
)


def WallRuns(Slabs: tuple[PrismSlab, ...]) -> list[tuple[KPlaneLoop, float, float]]:
    RunList: list[tuple[KPlaneLoop, float, float]] = []
    for Index, SlabValue in enumerate(Slabs):
        for LoopValue in SlabValue.Loops:
            if Index and LoopValue in Slabs[Index - 1].Loops:
                continue
            LastValue = Index
            while (
                LastValue + 1 < len(Slabs) and LoopValue in Slabs[LastValue + 1].Loops
            ):
                LastValue += 1
            RunList.append((LoopValue, SlabValue.LowerCm, Slabs[LastValue].UpperCm))
    return RunList


def WallFor(
    SpanValue: KPlaneSpan,
    Joints: tuple[tuple[float, float], ...],
    Lower: float,
    Upper: float,
) -> WallFace:
    Bottom = LevelEdge(SpanValue, Lower)
    TopValue = LevelEdge(SpanValue, Upper)
    if IsFullCircle(SpanValue):
        Loops = ((ShapeUse(Bottom, True),), (ShapeUse(TopValue, False),))
        return WallFace(SpanValue, Lower, Upper, Loops)
    RingValue = (
        ShapeUse(Bottom, True),
        ShapeUse(RiseEdge(Joints[1], Lower, Upper), True),
        ShapeUse(TopValue, False),
        ShapeUse(RiseEdge(Joints[0], Lower, Upper), False),
    )
    return WallFace(SpanValue, Lower, Upper, (RingValue,))


def WallFaces(Slabs: tuple[PrismSlab, ...]) -> tuple[WallFace, ...]:
    return tuple(
        WallFor(
            SpanValue,
            (SpanFinish(LoopValue[Index - 1]), SpanFinish(SpanValue)),
            Lower,
            Upper,
        )
        for LoopValue, Lower, Upper in WallRuns(Slabs)
        for Index, SpanValue in enumerate(LoopValue)
    )
