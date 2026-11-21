from math import dist as Distance

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AngleGeometry import (
    AngleGeometry,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDiff,
    DatumDot,
    DatumOffset,
    DatumPoint,
    DatumUnit,
    KDatumVector,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleGeom import (
    KWitnessRadius,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)

# the ordinary native arc branch uses a distinct solver limit for witness separation
KArcTolerance = 1e-8


# short presentation residual checks compare metric points at the measured length precision
KArcLengthError = 1e-14


# witness endpoints keep their own transformed coordinate in the dimension frame
def ArcLocal(Geometry: AngleGeometry, PointValue: KDatumVector) -> KDatumVector:
    FrameValue, Shift = Geometry.DimensionValue, Geometry.ShiftValue
    return (
        DatumDot(PointValue, FrameValue.AxisU) + Shift[0],
        DatumDot(PointValue, FrameValue.AxisV) + Shift[1],
        DatumDot(PointValue, FrameValue.NormalValue) + Shift[2],
    )


# intersecting ordered witness rays recover the actual annotation centre
def ArcCenter(
    First: KDatumVector,
    Other: KDatumVector,
    FirstRay: KDatumVector,
    OtherRay: KDatumVector,
) -> KDatumVector:
    Cosine = DatumDot(FirstRay, OtherRay)
    if 1.0 - abs(Cosine) < KArcTolerance:
        raise ValueError("parallel angular witnesses require a different centre branch")
    Displacement = DatumDiff(Other, First)
    Scaled = DatumOffset(KHingeRoot, Displacement, Cosine)
    ScaleValue = 1.0 / (1.0 - Cosine * Cosine)
    Travel = (
        DatumDot(Displacement, FirstRay) - DatumDot(Scaled, OtherRay)
    ) * ScaleValue
    return DatumOffset(First, FirstRay, Travel)


# arc geometry remains derived from the current angular witnesses and label direction
def MakeAngleArc(Geometry: AngleGeometry, AngleValue: float) -> dict[str, object]:
    First, Other, Anchor = (
        ArcLocal(Geometry, PointValue) for PointValue in Geometry.WitnessValues
    )
    if any(
        abs(Distance(PointValue, Anchor) - KWitnessRadius) > KArcLengthError
        for PointValue in (First, Other)
    ):
        raise ValueError(
            "angular witnesses must retain their full length in the dimension frame"
        )
    FirstIn = DatumUnit(DatumDiff(Anchor, First))
    OtherIn = DatumUnit(DatumDiff(Anchor, Other))
    Center = ArcCenter(First, Other, FirstIn, OtherIn)
    if Distance(Center, Anchor) > KArcLengthError:
        raise ValueError(
            "nonintersecting witnesses are outside the ordinary angular display"
        )
    FirstRay = (-FirstIn[0], -FirstIn[1], -FirstIn[2])
    OtherRay = (-OtherIn[0], -OtherIn[1], -OtherIn[2])
    Crossing = CrossVector(FirstRay, OtherRay)
    if Crossing[2] <= KArcTolerance:
        raise ValueError(
            "ordinary angular arc requires its canonical signed witness order"
        )
    Label = DatumOffset(KHingeRoot, Geometry.LabelValue, Geometry.RadiusValue)
    Offset = DatumDiff(Label, Center)
    Direction = DatumUnit(Offset)
    if DatumDot(CrossVector(FirstRay, Direction), Crossing) >= -KArcTolerance:
        raise ValueError("ordinary angular arc requires an exterior label")
    AnchorDelta = DatumDiff(Anchor, Center)
    return {
        "f880": DatumPoint(Direction),
        "f8a8": -0.5,
        "f8b0": Distance(Offset, KHingeRoot),
        "f958": DatumPoint(First),
        "f970": DatumPoint(Anchor),
        "f988": DatumPoint(Other),
        "f9a0": DatumPoint(Anchor),
        "f9b8": DatumPoint(Center),
        "fad0": Geometry.Separation,
        "f100c": 1,
        "f1010": 1,
        "f1008": int(AngleValue <= 3.1415926435898003),
        "ffb8": DatumPoint(FirstRay),
        "ffd0": DatumPoint(OtherRay),
        "ffe8": DatumDot(AnchorDelta, FirstRay),
        "fff0": DatumDot(DatumDiff(First, Center), FirstRay),
        "fff8": DatumDot(AnchorDelta, OtherRay),
        "f1000": DatumDot(DatumDiff(Other, Center), OtherRay),
        "f1018": 0x18,
    }
