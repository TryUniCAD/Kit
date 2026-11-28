from math import (
    cos as Cosine,
    dist as Distance,
    isfinite as IsFinite,
    pi as CircleRatio,
    sin as SinValue,
)

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AngleGeometry import (
    AngleGeometry,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumLine import (
    DatumLine,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDiff,
    DatumDot,
    DatumOffset,
    DatumUnit,
    KDatumVector,
    KHingeAxis,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)

# the measured construction uses a one millimetre witness from the actual angular vertex
KWitnessRadius = 0.001


# the selected right support starts with the canonical positive world x normal
KRightNormal: KDatumVector = (1.0, 0.0, 0.0)


# the acute positive angle rotates the actual right plane around its directed finite hinge
def MakeAngleGeom(
    StartValue: KDatumVector, EndValue: KDatumVector, AngleValue: float
) -> AngleGeometry:
    if (
        type(AngleValue) is not float
        or not 0.0 < AngleValue < CircleRatio / 2.0
        or StartValue[:2] != KHingeRoot[:2]
        or EndValue[:2] != KHingeRoot[:2]
        or not all(IsFinite(Value[2]) for Value in (StartValue, EndValue))
        or not StartValue[2] > 0.0 > EndValue[2]
    ):
        raise ValueError(
            "angular plane requires an acute right angle on a directed through origin hinge"
        )
    Lower, Upper = -StartValue[2], -EndValue[2]
    Length = Upper - Lower
    if not IsFinite(Length) or Length <= 1e-7:
        raise ValueError("angular plane requires a measurable finite hinge")
    Margin = Length * 0.05
    Borders = (Upper + Margin, Lower - Margin, Length + Margin, -Margin)
    Lateral = DatumOffset(KHingeRoot, KRightNormal, Cosine(AngleValue))
    Normal = DatumUnit(
        DatumOffset(
            Lateral, CrossVector(KHingeAxis, KRightNormal), SinValue(AngleValue)
        )
    )
    Vertical = DatumUnit(CrossVector(Normal, KHingeAxis))
    PlaneValue = PlaneFrame(KHingeRoot, KHingeAxis, Vertical, Normal)
    Center, _, _ = DatumLine(PlaneValue, Borders)
    Corner = DatumOffset(
        DatumOffset(KHingeRoot, KHingeAxis, Borders[1]), Vertical, Borders[2]
    )
    FirstRay = DatumUnit(CrossVector(KRightNormal, KHingeAxis))
    DimAxis = DatumUnit(CrossVector(FirstRay, KHingeAxis))
    DimFrame = PlaneFrame(Center, DimAxis, FirstRay, KHingeAxis)
    Shift = (
        -DatumDot(Center, DimAxis),
        -DatumDot(Center, FirstRay),
        -DatumDot(Center, KHingeAxis),
    )
    First = DatumOffset(Center, FirstRay, KWitnessRadius)
    Other = DatumOffset(Center, Vertical, KWitnessRadius)
    Bisector = DatumUnit(DatumOffset(FirstRay, Vertical, 1.0))
    Label = DatumOffset(KHingeRoot, Bisector, KWitnessRadius)
    Relative = DatumDiff(Label, Center)
    Offset = (DatumDot(Relative, DimAxis), DatumDot(Relative, FirstRay), 0.0)
    return AngleGeometry(
        PlaneValue,
        Borders,
        Corner,
        DimFrame,
        Shift,
        (First, Other, Center),
        DatumUnit(Offset),
        Distance(Offset, KHingeRoot),
        Distance(First, Other),
    )
