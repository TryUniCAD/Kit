from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


@MakeDataClass(frozen=True, slots=True)
class ParCurve:
    Cache: NubsCurve
    FitTolerance: float
    SupportFlag: bool
    Support: TsplineSurf | SubtypeRef
    Bounds: tuple[float | None, float | None, float | None, float | None]
