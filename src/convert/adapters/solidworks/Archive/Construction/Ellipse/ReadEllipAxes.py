from math import atan2 as AtanAngle
from math import degrees as ToDegrees
from math import hypot as HypotValue
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.geometry.Models.GeometryConics import EllipseGeometry


# the major station and counterclockwise minor station preserve the admitted signed ellipse geometry
def ReadEllipAxes(
    GeometryValue: EllipseGeometry, DepthValue: float
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    MajorX = RequireScalar(GeometryValue.major_axis.x)
    MajorY = RequireScalar(GeometryValue.major_axis.y)
    if not IsClose(HypotValue(MajorX, MajorY), 1.0, rel_tol=0.0, abs_tol=1e-13):
        raise ValueError("cold ellipse requires an actual unit major direction")
    CenterX = RequireScalar(GeometryValue.center.x)
    CenterY = RequireScalar(GeometryValue.center.y)
    RadiusA = RequireScalar(GeometryValue.major_radius)
    RadiusB = RequireScalar(GeometryValue.minor_radius)
    AngleValue = abs(ToDegrees(AtanAngle(MajorY, MajorX)))
    if not (
        1 <= abs(CenterX) <= 80
        and 1 <= abs(CenterY) <= 80
        and 5 <= RadiusB < RadiusA <= 55
        and 1.2 <= RadiusA / RadiusB <= 3
        and 10 <= AngleValue <= 70
        and 0.003 <= DepthValue <= 0.055
    ):
        raise ValueError(
            "cold ellipse is outside the measured signed geometry and depth scope"
        )
    CenterValue = (CenterX / 1000, CenterY / 1000)
    MajorValue = (
        CenterValue[0] + RadiusA / 1000 * MajorX,
        CenterValue[1] + RadiusA / 1000 * MajorY,
    )
    MinorValue = (
        CenterValue[0] - RadiusB / 1000 * MajorY,
        CenterValue[1] + RadiusB / 1000 * MajorX,
    )
    return CenterValue, MajorValue, MinorValue
