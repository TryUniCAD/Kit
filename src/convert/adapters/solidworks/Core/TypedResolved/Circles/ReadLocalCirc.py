from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadCircleShape import (
    ReadCircleShape,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadRadialDrive import (
    ReadRadialDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a simple local circle must derive geometry and both solver owners from the linked native sketch fields
def ReadLocalCirc(
    SketchValue: ArchiveNode, LinkValue: NativeLink, AllowFree: bool = False
) -> tuple[LocalCircle, NativeDimension | None] | None:
    FieldsValue = SketchValue.FieldsValue
    CheckLineScope({**FieldsValue, "arcs": ()}, HasDrivers=True)
    Shape = ReadCircleShape(SketchValue)
    Drive = ReadRadialDrive(LinkValue, SketchValue)
    if Shape is None or (
        Drive is None and (not AllowFree or not IsLineState(FieldsValue["dims"]))
    ):
        return None
    ProfileValue, CenterIndex = Shape
    CenterX, CenterY, RadiusValue = ProfileValue.coordinates
    Dimension, ModeValue, _ = Drive if Drive is not None else (None, None, None)
    if Dimension is not None and not IsClose(
        Dimension.value_mm,
        RadiusValue * (2 if ModeValue == "diameter" else 1),
        rel_tol=1e-12,
        abs_tol=1e-10,
    ):
        return None
    CenterMark, ArcMark = ReadCircleMarks(SketchValue, CenterIndex, Drive is not None)
    return (
        LocalCircle(
            (CenterX, CenterY),
            RadiusValue,
            ArcMark,
            CenterMark,
            ModeValue,
            None if Dimension is None else Dimension.name,
            NativeNodeSpan(LinkValue, SketchValue),
        ),
        Dimension,
    )


# the local handles distinguish a free centre from an actual fixed point relation
def ReadCircleMarks(
    SketchValue: ArchiveNode, CenterIndex: int, IsFixed: bool
) -> tuple[int, int]:
    FieldsValue = SketchValue.FieldsValue
    ManagerValue = NativeRecord(FieldsValue["dims"])
    Relations = NativeRows(ManagerValue["log_g1"])
    if len(Relations) != int(IsFixed) or any(
        ManagerValue[NameValue] for NameValue in ("log_g2", "log_g3")
    ):
        raise ValueError("ordinary circle has an unexpected centre relation")
    if IsFixed:
        Relation = NativeRecord(Relations[0]["d"])
        Handle = RequireNative(Relation["h1"], "sgPointHandle")
        if Relation["f80"] != 17 or Handle.FieldsValue["idx"] != CenterIndex:
            raise ValueError("circle fix does not retain the actual centre")
    PointsValue = NativeRows(FieldsValue["points"])
    Center = NativeRecord(PointsValue[CenterIndex]["point"])
    ArcValue = NativeRecord(NativeRows(FieldsValue["arcs"])[0]["arc"])
    CenterMark, ArcMark = Center.get("f0c"), ArcValue.get("f0c")
    if (
        any(PointValue["kind"] != 0 for PointValue in PointsValue)
        or Center.get("f20") != int(IsFixed)
        or ArcValue.get("f20") != int(IsFixed)
        or type(CenterMark) is not int
        or type(ArcMark) is not int
        or min(CenterMark, ArcMark) < 1
    ):
        raise ValueError("ordinary circle lacks explicit local arc and point identity")
    return CenterMark, ArcMark
