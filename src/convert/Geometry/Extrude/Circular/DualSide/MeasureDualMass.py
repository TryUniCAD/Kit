from math import fsum as SumValues, isfinite as IsFinite

from convert.Geometry.Extrude.Circular.DualSide.DualFrame import DualFrame
from convert.Geometry.Extrude.Circular.DualSide.DualMeridian import DualMeridian
from convert.Geometry.Extrude.Circular.DualSide.DualMoments import DualMoments
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# the full world origin tensor must preserve rotation translation and cross terms
def MeasureDualMass(
    FrameValue: Transform,
    Profile: CircleGeometry,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
) -> tuple[SpaceVector, SpaceVector]:
    Frame = DualFrame(FrameValue, Profile)
    Meridian = DualMeridian(Profile.radius, FirstMm, SecondMm, FirstTaper, SecondTaper)
    Origin = (Frame.origin.x, Frame.origin.y, Frame.origin.z)
    AxisValue = (Frame.z_axis.x, Frame.z_axis.y, Frame.z_axis.z)
    try:
        Volume, Moment, Radial, Axial = DualMoments(Meridian)
        Tensor = tuple(
            tuple(
                SumValues(
                    (
                        Radial if First == Second else 0.0,
                        (Axial - Radial) * AxisValue[First] * AxisValue[Second],
                        Volume * Origin[First] * Origin[Second],
                        Moment
                        * (
                            Origin[First] * AxisValue[Second]
                            + AxisValue[First] * Origin[Second]
                        ),
                    )
                )
                for Second in range(3)
            )
            for First in range(3)
        )
        Diagonal = tuple(
            SumValues(Tensor[Index][Index] for Index in range(3) if Index != First)
            for First in range(3)
        )
        CrossTerms = tuple(
            -Tensor[First][Second] for First, Second in ((0, 1), (0, 2), (1, 2))
        )
    except OverflowError as ErrorValue:
        raise ValueError("Circular side tensor exceeds finite geometry") from ErrorValue
    if (
        not all(IsFinite(Value) for Value in (*Diagonal, *CrossTerms))
        or min(Diagonal) <= 0
    ):
        raise ValueError("Circular side tensor requires finite positive inertia")
    return SpaceVector(*Diagonal), SpaceVector(*CrossTerms)
