from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import IsInRegion
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SideProbe import SideProbe


def CapRings(
    Level: float, Upward: bool, Below: PrismSlab | None, Above: PrismSlab | None
) -> list[tuple[KPlaneLoop, bool]]:
    BelowLoops = () if Below is None else Below.Loops
    AboveLoops = () if Above is None else Above.Loops
    Minuend, Subtrahend = (
        (BelowLoops, AboveLoops) if Upward else (AboveLoops, BelowLoops)
    )
    Candidates = [
        LoopValue for LoopValue in BelowLoops if LoopValue not in AboveLoops
    ] + [LoopValue for LoopValue in AboveLoops if LoopValue not in BelowLoops]
    Rings: list[tuple[KPlaneLoop, bool]] = []
    for LoopValue in Candidates:
        LeftPoint, RightPoint = SideProbe(LoopValue[0])
        LeftIn = IsInRegion(Minuend, LeftPoint) and not IsInRegion(
            Subtrahend, LeftPoint
        )
        RightIn = IsInRegion(Minuend, RightPoint) and not IsInRegion(
            Subtrahend, RightPoint
        )
        if LeftIn == RightIn:
            continue
        Rings.append((LoopValue, LeftIn == Upward))
    return Rings


def RingUses(
    LoopValue: KPlaneLoop, Forward: bool, Level: float
) -> tuple[ShapeUse, ...]:
    if Forward:
        return tuple(
            ShapeUse(LevelEdge(SpanValue, Level), True) for SpanValue in LoopValue
        )
    return tuple(
        ShapeUse(LevelEdge(SpanValue, Level), False)
        for SpanValue in reversed(LoopValue)
    )
