from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
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
    SketchValue: ArchiveNode, LinkValue: NativeLink
) -> tuple[LocalCircle, NativeDimension] | None:
    FieldsValue = SketchValue.FieldsValue
    CheckLineScope({**FieldsValue, "arcs": ()}, HasDrivers=True)
    Shape = ReadCircleShape(SketchValue)
    Drive = ReadRadialDrive(LinkValue, SketchValue)
    if Shape is None or Drive is None:
        return None
    ProfileValue, CenterIndex = Shape
    Dimension, ModeValue, _ = Drive
    CenterX, CenterY, RadiusValue = ProfileValue.coordinates
    if not IsClose(
        Dimension.value_mm,
        RadiusValue * (2 if ModeValue == "diameter" else 1),
        rel_tol=1e-12,
        abs_tol=1e-10,
    ):
        return None
    CenterMark, ArcMark = ReadCircleMarks(SketchValue, CenterIndex)
    return (
        LocalCircle(
            (CenterX, CenterY),
            RadiusValue,
            ArcMark,
            CenterMark,
            ModeValue,
            Dimension.name,
            NativeNodeSpan(LinkValue, SketchValue),
        ),
        Dimension,
    )


# fixing the actual centre means one typed unary point relation and one use of each retained geometry owner
def ReadCircleMarks(SketchValue: ArchiveNode, CenterIndex: int) -> tuple[int, int]:
    FieldsValue = SketchValue.FieldsValue
    ManagerValue = NativeRecord(FieldsValue["dims"])
    Relations = NativeRows(ManagerValue["log_g1"])
    if len(Relations) != 1 or any(
        ManagerValue[NameValue] for NameValue in ("log_g2", "log_g3")
    ):
        raise ValueError("ordinary circle requires its one actual fixed centre")
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
        or Center.get("f20") != 1
        or ArcValue.get("f20") != 1
        or type(CenterMark) is not int
        or type(ArcMark) is not int
        or min(CenterMark, ArcMark) < 1
    ):
        raise ValueError("ordinary circle lacks explicit local arc and point identity")
    return CenterMark, ArcMark
