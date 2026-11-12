from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapRings import RingUses
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    LoopArea,
    LoopPolygon,
    WindNumber,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanStart


def GroupRings(
    Rings: list[tuple[KPlaneLoop, bool]], Upward: bool, Level: float = 0.0
) -> list[tuple[tuple[ShapeUse, ...], ...]]:
    Outer = [
        (LoopValue, Forward)
        for LoopValue, Forward in Rings
        if (LoopArea(LoopValue) * (1.0 if Forward else -1.0) > 0) == Upward
    ]
    Holes = [RingValue for RingValue in Rings if RingValue not in Outer]
    Groups: dict[int, list[tuple[KPlaneLoop, bool]]] = {
        Index: [RingValue] for Index, RingValue in enumerate(Outer)
    }
    for LoopValue, Forward in Holes:
        Point = SpanStart(LoopValue[0])
        Hosts = [
            Index
            for Index, RingValue in enumerate(Outer)
            if WindNumber(LoopPolygon(RingValue[0]), Point) != 0
        ]
        if not Hosts:
            raise ValueError("Fusion part cap boundary has no enclosing outer loop")
        Smallest = min(Hosts, key=lambda Index: abs(LoopArea(Outer[Index][0])))
        Groups[Smallest].append((LoopValue, Forward))
    return [
        tuple(RingUses(LoopValue, Forward, Level) for LoopValue, Forward in Members)
        for Members in Groups.values()
    ]
