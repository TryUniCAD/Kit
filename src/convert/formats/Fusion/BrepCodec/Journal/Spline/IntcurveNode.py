from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Spline.ExactCurve import ExactCurve


@MakeDataClass(frozen=True, slots=True)
class IntcurveNode:
    Prefix: EntityPrefix
    Reversed: bool
    Curve: ExactCurve
    Lower: float | None
    Upper: float | None
