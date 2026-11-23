from math import dist as Distance, isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDiff,
    DatumDot,
    DatumOffset,
    DatumPoint,
    KDatumVector,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PrincDrive import (
    PrincDrive,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# pitch geometry derives the displayed length and text placement from the actual two witness points
def SetPatPointMut(
    Dimension: ArchiveNode,
    Fields: dict[str, object],
    Witnesses: tuple[KDatumVector, KDatumVector],
    PrincipalValue: PrincDrive | None,
) -> None:
    Start, Finish = Witnesses
    SpanValue = Distance(Start, Finish)
    Delta = DatumDiff(Finish, Start)
    Squares = DatumDot(Delta, Delta)
    if (
        not IsFinite(SpanValue)
        or SpanValue <= 0.0
        or Squares <= 0.0
        or not IsFinite(Squares)
    ):
        raise ValueError("pitch display must retain distinct actual witness positions")
    Midpoint = DatumOffset(Start, Delta, 0.5)
    Relative = DatumDiff(Midpoint, Start)
    PointFields = Dimension.FieldsValue
    PointFields.update(
        f80=DatumPoint(Start), fa0=DatumPoint(Finish), fc0=DatumPoint(KHingeRoot)
    )
    if PrincipalValue is None:
        Position = DatumDot(Relative, Delta) / Squares
    else:
        FrameValue = PrincipalValue.FrameValue
        PointFields.update(
            has_fe0=1,
            fe0=DatumPoint(FrameValue.AxisU),
            fe8=DatumPoint(PrincipalValue.SketchNormal),
            has_ff0=1,
            ff0=FrameXform(FrameValue),
        )
        Position = DatumDot(Relative, FrameValue.AxisU) / SpanValue
    Fields.update(
        f880=MakePoint(YValue=1.0),
        fa38=MakePoint(XValue=1.0),
        f988=MakePoint(XValue=SpanValue),
        f9a0=MakePoint(XValue=SpanValue),
        fad0=SpanValue,
        f8a8=Position,
    )
