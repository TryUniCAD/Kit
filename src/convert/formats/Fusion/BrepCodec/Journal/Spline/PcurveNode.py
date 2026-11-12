from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Spline.ParCurve import ParCurve


@MakeDataClass(frozen=True, slots=True)
class PcurveNode:
    Prefix: EntityPrefix
    Reversed: bool
    Curve: ParCurve
    OffsetU: float
    OffsetV: float
