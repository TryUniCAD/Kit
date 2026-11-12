from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


@MakeDataClass(frozen=True, slots=True)
class NubsCurve:
    Degree: int
    Closure: int
    Knots: tuple[SplineKnot, ...]
    Points: tuple[tuple[float, ...], ...]
