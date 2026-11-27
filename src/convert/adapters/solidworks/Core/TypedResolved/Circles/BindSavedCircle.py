from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.ApplyCircle import (
    ApplyCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.ReadLinkedName import (
    ReadLinkedName,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckBlindCirc import (
    CheckBlindCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckCircChain import (
    CheckCircChain,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadCirclePlane import (
    ReadCirclePlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.SavedCircleAtom import (
    SavedCircleAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckSingleBoss import (
    CheckSingleBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircDrive import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# one saved circle binds its live dimension handles to the actual profile support and producing atom
def BindSavedCircle(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    Profile: ArchiveNode,
    Archive: SldprtArchive,
) -> NativeModel:
    SketchValue, Operation = ModelValue.sketches[0], ModelValue.operations[0]
    CheckSingleBoss(Features, "moExtrusion_c")
    if Features[SketchValue.object_id] is not Profile:
        raise ValueError("saved circle profile does not alias its public sketch")
    Owner = ReadExtrude(LinkValue, Features[Operation.object_id], Features)
    if Owner.ProfileValue is not Profile or Operation.kind != "join":
        raise ValueError("saved circle lacks its actual creating profile")
    ShapeValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    Shape = ReadLocalCirc(ShapeValue, LinkValue)
    if Shape is None:
        raise ValueError("saved circle has no complete local radial driver")
    CircleValue, Driver = Shape
    if Driver is None or CircleValue.ModeValue not in ("diameter", "radius"):
        raise ValueError("saved circle requires a measured driven front profile")
    AttachedBody = CircleValue.ModeValue == "radius"
    SavedBody = not AttachedBody or Profile.FieldsValue.get("f3c0") == 1
    CheckPrismProf(Profile, IsSaved=SavedBody)
    Dimension, Parameter, Inactive = CheckBlindCirc(
        Owner, SavedBody=SavedBody, AttachedBody=AttachedBody
    )
    CheckCircDrive(ShapeValue)
    if SavedBody:
        CheckCircChain(Profile, CircleValue.ArcMark)
    FrameValue, PlaneId = ReadCirclePlane(ModelValue, LinkValue, Features, Profile)
    BodyId = SavedCircleAtom(LinkValue, Owner.NodeValue)
    Bound = ReplaceValue(
        SketchValue,
        support_plane_id=PlaneId,
        TypedFrame=FrameValue,
        TypedCircle=CircleValue,
        dimensions=(Driver,),
    )
    DepthValue = {
        **NativeNodeSpan(LinkValue, Parameter),
        "dimension_index": Dimension.IndexValue,
        "slot": "f818.f20",
        "value_field": "f58",
        "value_m": Inactive,
    }

    BoundModel = ApplyCircle(ModelValue, Bound, Owner, InactiveDepth=DepthValue)
    BodyName, Cylinder = (
        ReadLinkedName(
            LinkValue,
            Owner,
            CircleValue,
            Inactive,
            BodyId,
            Archive,
            BoundModel,
            SavedBody,
        )
        if AttachedBody
        else (None, None)
    )
    return ReplaceValue(
        BoundModel,
        SavedCircleAtom=BodyId,
        SavedCircleName=BodyName,
        AttachedCylinderValue=Cylinder,
    )
