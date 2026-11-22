from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwArc import ReadSwArc
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwDriver import (
    ReadSwDriver,
    SwDriver,
)
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorSpace import SpaceVector


# each authored contour retains its independent datum and editable radial owner
@DataClass(frozen=True, slots=True)
class SwReadProfile:
    FeatureValue: ArchiveNode
    CurveValue: CircleGeometry | ArcGeometry
    DriverValue: SwDriver
    DatumId: int


# the actual local component stamp must match the selected profile and its header creation log
def ReadSwPick(
    LinkValue: NativeLink, WrapperValue: ArchiveNode, ProfileValue: ArchiveNode
) -> int:
    PartValue = LinkValue.ConfigValue.RootValue
    Selector = RequireNative(WrapperValue.FieldsValue.get("f58"), "moCompProfile_c")
    Component = RequireNative(Selector.FieldsValue.get("f58"), "moUnitComponent_c")
    ProfileId = NativeNodeId(ProfileValue)
    GhostId = Selector.FieldsValue.get("f20")
    if (
        Selector.FieldsValue.get("ff0")
        != {
            "f00": ProfileId,
            "f08": DatumTime(LinkValue.ConfigValue.HeaderValue, ProfileId),
        }
        or Component.FieldsValue.get("owner") is not PartValue
        or Component.FieldsValue.get("has_ext") != 0
        or type(GhostId) is not int
        or GhostId <= 0
    ):
        raise ValueError(
            "SOLIDWORKS sweep pick does not reference its actual local profile"
        )
    return GhostId


# the profile scope retains its measured orientation and independently owned editable geometry
def ReadSwProfile(
    LinkValue: NativeLink,
    FeatureValue: ArchiveNode,
    NodeValues: Mapping[int, ArchiveNode],
    IsSection: bool,
) -> SwReadProfile:
    SupportValue = RequireNative(
        FeatureValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    DatumId = NativeRecord(SupportValue.FieldsValue.get("ff0")).get("f00")
    FrameValue = ReadPrismFrame(
        FeatureValue, LinkValue.ConfigValue.RootValue, NodeValues, FrontOnly=False
    )
    if (
        type(DatumId) is not int
        or DatumId not in NodeValues
        or ReadNativeName(NodeValues[DatumId])
        != ("Right Plane" if IsSection else "Front Plane")
        or FrameValue.z_axis
        != (SpaceVector(1.0, 0.0, 0.0) if IsSection else SpaceVector(0.0, 0.0, 1.0))
    ):
        raise ValueError("SOLIDWORKS sweep sketch has an alternate support plane")
    SketchValue = RequireNative(FeatureValue.FieldsValue.get("pd_f80"), "sgSketch")
    DriverValue = ReadSwDriver(SketchValue, IsSection)
    RadiusValue = (
        DriverValue.MetresValue / 2.0 if IsSection else DriverValue.MetresValue
    )
    return SwReadProfile(
        FeatureValue,
        ReadSwArc(SketchValue, RadiusValue, IsSection),
        DriverValue,
        DatumId,
    )
