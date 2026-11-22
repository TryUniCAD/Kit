from math import sqrt as SquareRoot

from interchange.brep.Curves.BrepCurves import BrepCurve, LineCurve, NurbsCurve
from interchange.brep.Curves.BrepPcurves import BrepPcurve, LinePcurve, NurbsPcurve
from interchange.brep.Surfaces.BrepSurfaces import (
    BrepSurface,
    NurbsSurface,
    PlaneSurface,
)
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# four clamped rational quadratic quarters have double internal knots
KEllipKnots = (0.0, 1.0, 2.0, 3.0, 4.0)

# the first and fourth quarters meet at the distinct owned major station
KEllipMults = (3, 2, 2, 2, 3)

# rational quarter weights represent the conic without sampled approximations
KEllipWeights = tuple(1.0 if Index % 2 == 0 else SquareRoot(0.5) for Index in range(9))


# control corners are intersections of consecutive axis station tangents
def EllipControls(Ellipse: EllipseGeometry) -> tuple[tuple[float, float], ...]:
    RadiusA, RadiusB = Ellipse.major_radius, Ellipse.minor_radius
    return (
        (RadiusA, 0.0),
        (RadiusA, RadiusB),
        (0.0, RadiusB),
        (-RadiusA, RadiusB),
        (-RadiusA, 0.0),
        (-RadiusA, -RadiusB),
        (0.0, -RadiusB),
        (RadiusA, -RadiusB),
        (RadiusA, 0.0),
    )


# the signed sketch frame fixes the radial coordinates of both sections
def EllipSection(Ellipse: EllipseGeometry, HeightMm: float) -> tuple[SpaceVector, ...]:
    Center, Major = Ellipse.center, Ellipse.major_axis
    return tuple(
        SpaceVector(
            Center.x + First * Major.x - Second * Major.y,
            Center.y + First * Major.y + Second * Major.x,
            HeightMm,
        )
        for First, Second in EllipControls(Ellipse)
    )


# the clamped boundary has the same rim parameter on both planar caps and wall
def EllipCurves(
    Lower: tuple[SpaceVector, ...],
    Upper: tuple[SpaceVector, ...],
) -> tuple[BrepCurve, ...]:
    return (
        NurbsCurve(
            "ellipse-lower-curve", 2, Lower, KEllipKnots, KEllipMults, KEllipWeights
        ),
        NurbsCurve(
            "ellipse-upper-curve", 2, Upper, KEllipKnots, KEllipMults, KEllipWeights
        ),
        LineCurve("ellipse-seam-curve", Lower[0], SpaceVector(0.0, 0.0, 1.0)),
    )


# a tensor product of the exact conic and blind translation gives the full lateral face
def EllipSurfaces(
    Ellipse: EllipseGeometry,
    Lower: tuple[SpaceVector, ...],
    Upper: tuple[SpaceVector, ...],
) -> tuple[BrepSurface, ...]:
    Center, Major = Ellipse.center, Ellipse.major_axis
    HeightMm = Upper[0].z
    Direction = SpaceVector(Major.x, Major.y, 0.0)
    return (
        PlaneSurface(
            "ellipse-lower-surface",
            SpaceVector(Center.x, Center.y, 0.0),
            SpaceVector(0.0, 0.0, -1.0),
            Direction,
        ),
        PlaneSurface(
            "ellipse-upper-surface",
            SpaceVector(Center.x, Center.y, HeightMm),
            SpaceVector(0.0, 0.0, 1.0),
            Direction,
        ),
        NurbsSurface(
            "ellipse-wall-surface",
            2,
            1,
            tuple(
                (Bottom, UpperValue)
                for Bottom, UpperValue in zip(Lower, Upper, strict=True)
            ),
            KEllipKnots,
            (0.0, HeightMm),
            KEllipMults,
            (2, 2),
            tuple((Weight, Weight) for Weight in KEllipWeights),
        ),
    )


# opposite cap normals and the two parameter sides of the same seam require separate trims
def EllipPcurves(Ellipse: EllipseGeometry, HeightMm: float) -> tuple[BrepPcurve, ...]:
    Lower, Upper = (
        NurbsPcurve(
            f"ellipse-{NameValue}-trim",
            2,
            tuple(
                PlaneVector(First, SignValue * Second)
                for First, Second in EllipControls(Ellipse)
            ),
            KEllipKnots,
            KEllipMults,
            KEllipWeights,
        )
        for NameValue, SignValue in (("lower", -1.0), ("upper", 1.0))
    )
    return (
        Lower,
        Upper,
        LinePcurve("ellipse-bottom-trim", PlaneVector(0.0, 0.0), PlaneVector(1.0, 0.0)),
        LinePcurve(
            "ellipse-far-seam-trim",
            PlaneVector(KEllipKnots[-1], 0.0),
            PlaneVector(0.0, 1.0),
        ),
        LinePcurve(
            "ellipse-top-trim", PlaneVector(0.0, HeightMm), PlaneVector(1.0, 0.0)
        ),
        LinePcurve(
            "ellipse-near-seam-trim", PlaneVector(0.0, 0.0), PlaneVector(0.0, 1.0)
        ),
    )
