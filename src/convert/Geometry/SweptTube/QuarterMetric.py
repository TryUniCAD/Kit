from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite, pi as PiValue

from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# the periodic tube has a finite analytic solid measure independent of carrier sampling
@DataClass(frozen=True, slots=True)
class QuarterMetric:
    VolumeValue: float
    AreaValue: float
    CenterValue: SpaceVector
    BoundsValue: BoundingBox


# moment integration preserves the offset from the centerline centroid of a finite radius tube
def MeasureQuarter(SectionRadius: float, PathRadius: float) -> QuarterMetric:
    if not 0.0 < SectionRadius < PathRadius or not IsFinite(PathRadius):
        raise ValueError("quarter tube requires two finite separated radii")
    AngleValue = PiValue / 2.0
    VolumeValue = PiValue * SectionRadius**2 * PathRadius * AngleValue
    AreaValue = (
        2.0 * PiValue * SectionRadius * (PathRadius * AngleValue + SectionRadius)
    )
    CenterX = (PathRadius + SectionRadius**2 / (4.0 * PathRadius)) / AngleValue
    return QuarterMetric(
        VolumeValue,
        AreaValue,
        SpaceVector(CenterX, PathRadius - CenterX, 0.0),
        BoundingBox(
            SpaceVector(0.0, -SectionRadius, -SectionRadius),
            SpaceVector(PathRadius + SectionRadius, PathRadius, SectionRadius),
        ),
    )
