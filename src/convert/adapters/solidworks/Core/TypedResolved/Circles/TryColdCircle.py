from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.ApplyCircle import (
    ApplyCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckBlindCirc import (
    CheckBlindCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckColdCirc import (
    CheckColdCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircDrive import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.VectorSpace import SpaceVector


# typed radial and depth values must travel with the linked profile and datum that actually own them
def BindColdCirc(
    ModelValue: NativeModel,
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    Profile: ArchiveNode,
) -> NativeModel:
    SketchValue, Operation = ModelValue.sketches[0], ModelValue.operations[0]
    Owner = ReadExtrude(
        LinkValue, Features[Operation.object_id], Features, AllowReverse=True
    )
    if Owner.ProfileValue is not Profile or Operation.kind != "join":
        raise ValueError("cold circle lacks its actual creating profile")
    CheckPrismProf(Profile)
    ShapeValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    Shape = ReadLocalCirc(ShapeValue, LinkValue)
    if Shape is None:
        raise ValueError("cold circle has no complete local radial driver")
    CircleValue, Driver = Shape
    if Driver is None:
        raise ValueError("cold circle has no complete local radial driver")
    CheckColdCirc(
        ModelValue,
        LinkValue,
        ReadCmgrMut(Archive.require("Contents/CMgr"), 19000),
        Features,
    )
    _ = CheckBlindCirc(Owner)
    CheckCircDrive(ShapeValue)
    FrameValue = ReadPrismFrame(
        Profile, LinkValue.ConfigValue.RootValue, Features, FrontOnly=False
    )
    Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if (
        type(PlaneId) is not int
        or not any(Plane.object_id == PlaneId for Plane in ModelValue.planes)
        or (FrameValue.z_axis, CircleValue.ModeValue, Owner.IsReversed)
        not in (
            (SpaceVector(0.0, 0.0, 1.0), "diameter", False),
            (SpaceVector(0.0, 1.0, 0.0), "radius", True),
        )
    ):
        raise ValueError("cold circle is outside the two qualified blind profiles")
    return ApplyCircle(
        ModelValue,
        ReplaceValue(
            SketchValue,
            support_plane_id=PlaneId,
            TypedFrame=FrameValue,
            TypedCircle=CircleValue,
            dimensions=(Driver,),
        ),
        Owner,
    )


# the cold route only substitutes analytic geometry when no saved kernel role exists
def TryColdCircle(
    ModelValue: NativeModel,
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    Profile: ArchiveNode,
) -> NativeModel | None:
    if not IsCacheAbsent(Archive):
        return None
    try:
        ShapeValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
        if not ShapeValue.FieldsValue.get("arcs"):
            return None
        return BindColdCirc(ModelValue, Archive, LinkValue, Features, Profile)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
