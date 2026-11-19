from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircEnd import (
    CheckCircEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircDrive import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircMode import (
    CheckCircMode,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircPublic import (
    CheckCircPublic,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircValues import (
    CheckCircValues,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleGeomPlan import (
    CircleGeomPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.ReadCircRange import (
    ReadCircRange,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the body uses the actual local circle and its typed end and datum owners after complete part admission
def ReadCircPlan(
    LinkValue: NativeLink, Features: Mapping[int, ArchiveNode], ModelValue: NativeModel
) -> CircleGeomPlan:
    (BossValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    OwnerValue = ReadExtrude(LinkValue, BossValue, Features)
    if OwnerValue.ParentsValue != (OwnerValue.ProfileValue,):
        raise ValueError("cache free circle has additional operation parents")
    CheckPrismAtom(BossValue)
    CheckBossState(BossValue)
    CheckCircEnd(OwnerValue)
    CheckCircValues(OwnerValue)
    CheckPrismProf(OwnerValue.ProfileValue)
    CheckPrismPlane(Features, LinkValue.ConfigValue.RootValue)
    SketchValue = RequireNative(
        OwnerValue.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch"
    )
    CheckCircDrive(SketchValue)
    ShapeValue = ReadLocalCirc(SketchValue, LinkValue)
    if ShapeValue is None:
        raise ValueError(
            "cache free circle lacks its actual radial driver and fixed centre"
        )
    CircleValue, Driver = ShapeValue
    if Driver is None:
        raise ValueError("cache free circle requires an actual radial driver")
    CheckCircPublic(ModelValue, Features, OwnerValue, CircleValue)
    FrameValue = ReadPrismFrame(
        OwnerValue.ProfileValue,
        LinkValue.ConfigValue.RootValue,
        Features,
        FrontOnly=False,
    )
    CheckCircMode(OwnerValue, CircleValue, FrameValue)
    Lower, Upper = ReadCircRange(OwnerValue)
    EvidenceValue = {
        "method": "typed_parametric_circular_boss",
        "model_version": 19000,
        "profile_owner": NativeNodeSpan(LinkValue, OwnerValue.ProfileValue),
        "boss_owner": NativeNodeSpan(LinkValue, BossValue),
        "radial_owner": Driver.TypedOwner,
        "depth_owner": OwnerValue.RequireDepth().DepthValue.TypedOwner,
        "native_kernel_identity": False,
        "axial_interval_mm": (Lower, Upper),
    }
    return CircleGeomPlan(
        FrameValue,
        CircleGeometry(PlaneVector(*CircleValue.CenterValue), CircleValue.RadiusValue),
        Lower,
        Upper,
        EvidenceValue,
    )
