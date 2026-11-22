from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.ApplyCircle import (
    ApplyCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckBlindCirc import (
    CheckBlindCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckCircChain import (
    CheckCircChain,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# one saved circle binds its live dimension handles to the actual profile support and producing atom
def BindSavedCircle(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    Profile: ArchiveNode,
) -> NativeModel:
    SketchValue, Operation = ModelValue.sketches[0], ModelValue.operations[0]
    CheckSingleBoss(Features, "moExtrusion_c")
    if Features[SketchValue.object_id] is not Profile:
        raise ValueError("saved circle profile does not alias its public sketch")
    CheckPrismProf(Profile, IsSaved=True)
    Owner = ReadExtrude(LinkValue, Features[Operation.object_id], Features)
    if Owner.ProfileValue is not Profile or Operation.kind != "join":
        raise ValueError("saved circle lacks its actual creating profile")
    Dimension, Parameter, Inactive = CheckBlindCirc(Owner, SavedBody=True)
    ShapeValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    Shape = ReadLocalCirc(ShapeValue, LinkValue)
    if Shape is None:
        raise ValueError("saved circle has no complete local radial driver")
    CircleValue, Driver = Shape
    if Driver is None or CircleValue.ModeValue != "diameter":
        raise ValueError("saved circle requires the measured front diameter branch")
    CheckCircDrive(ShapeValue)
    CheckCircChain(Profile, CircleValue.ArcMark)
    FrameValue = ReadPrismFrame(Profile, LinkValue.ConfigValue.RootValue, Features)
    Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int or not any(
        Plane.object_id == PlaneId for Plane in ModelValue.planes
    ):
        raise ValueError("saved circle has no owned front support datum")
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
    return ReplaceValue(
        ApplyCircle(ModelValue, Bound, Owner, InactiveDepth=DepthValue),
        SavedCircleAtom=BodyId,
    )
