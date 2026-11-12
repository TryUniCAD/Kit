from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve


@MakeDataClass(frozen=True, slots=True)
class ExactCurve:
    Revision: int
    Cache: NubsCurve
    FitTolerance: float
    CacheBounds: tuple[float | None, float | None]
    Jumps: tuple[tuple[float, ...], ...]
    Extension: int
    Ranges: tuple[float | None, float | None]
    TailCodes: tuple[int, int]
