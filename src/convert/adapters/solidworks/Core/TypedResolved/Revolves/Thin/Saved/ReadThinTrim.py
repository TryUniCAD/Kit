from math import cos as CosValue, sin as SinValue

from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.brep.Curves.BrepCurves import BrepCurve, CircleCurve, LineCurve


# the trim midpoint distinguishes the bounded arc from its complementary orbit
def ReadThinTrim(CurveValue: BrepCurve, Parameter: float) -> tuple[float, float, float]:
    if isinstance(CurveValue, LineCurve):
        PointValue = OffsetVector(CurveValue.origin, CurveValue.direction, Parameter)
    elif isinstance(CurveValue, CircleCurve):
        StartValue = OffsetVector(
            CurveValue.center,
            CurveValue.reference_direction,
            CurveValue.radius * CosValue(Parameter),
        )
        Tangent = CrossVector(CurveValue.axis, CurveValue.reference_direction)
        PointValue = OffsetVector(
            StartValue, Tangent, CurveValue.radius * SinValue(Parameter)
        )
    else:
        raise ValueError("SOLIDWORKS thin cache has an unsupported edge carrier")
    return PointValue.x, PointValue.y, PointValue.z
