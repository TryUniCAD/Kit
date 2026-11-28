from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircDrive import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircEnd import (
    CheckCircEnd,
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
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffBase import (
    ReadOffLink,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# the radial driver belongs to the actual translated sketch and must retain its fixed centre
def ReadOffProfile(
    SketchValue: NativeSketch,
    ProfileValue: ArchiveNode,
    LinkValue: NativeLink,
    FrameValue: PlaneFrame,
    OffsetId: int,
) -> CircleGeometry:
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    ReadOffLink(Reference, LinkValue.ConfigValue.RootValue, OffsetId, 0)
    CheckPrismProf(ProfileValue)
    ShapeValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    CheckCircDrive(ShapeValue)
    Shape = ReadLocalCirc(ShapeValue, LinkValue)
    if Shape is None or ProfileValue.FieldsValue.get("pd_ff0") != FrameXform(
        FrameValue
    ):
        raise ValueError("offset sketch does not reproduce its linked datum and circle")
    CircleValue, RadiusValue = Shape
    if (
        RadiusValue is None
        or RadiusValue.name != "D1"
        or CircleValue.ModeValue != "radius"
        or CircleValue.CenterValue != (0.0, 0.0)
        or SketchValue.TypedCircle != CircleValue
        or SketchValue.dimensions != (RadiusValue,)
        or SketchValue.support_plane_id != OffsetId
    ):
        raise ValueError(
            "offset circle requires its fixed centre and live radial driver"
        )
    return CircleGeometry(
        PlaneVector(*CircleValue.CenterValue), CircleValue.RadiusValue
    )


# the analytic cylinder must use the same live boss and translated frame as the public history
def ReadOffBoss(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    FrameValue: PlaneFrame,
    DatumId: int,
    OffsetId: int,
    Driver: DepthOwner,
) -> CircleGeomPlan:
    SketchValue, Operation = ModelValue.sketches[0], ModelValue.operations[0]
    Profile = RequireNative(Features[SketchValue.object_id], "moProfileFeature_c")
    CircleValue = ReadOffProfile(SketchValue, Profile, LinkValue, FrameValue, OffsetId)
    BossValue = Features[Operation.object_id]
    OwnerValue = ReadExtrude(LinkValue, BossValue, Features)
    CheckPrismAtom(BossValue)
    CheckBossState(BossValue)
    CheckCircEnd(OwnerValue)
    CheckCircValues(OwnerValue)
    Depth = OwnerValue.RequireDepth()
    if (
        OwnerValue.ProfileValue is not Profile
        or OwnerValue.ParentsValue != (Profile,)
        or OwnerValue.ModeValue != ExtrudeEnd.KBlind
        or OwnerValue.IsReversed
        or Operation.kind != "join"
        or Operation.extrusion_end != ExtrudeEnd.KBlind
        or Operation.direction_code != 0
        or Operation.profile_id != SketchValue.object_id
        or Driver.Parameter is Depth.Parameter
        or Depth.DepthValue.name != "D1"
        or not DatumId < OffsetId < SketchValue.object_id < Operation.object_id
    ):
        raise ValueError("offset profile requires its own forward blind boss")
    Lower, Upper = ReadCircRange(OwnerValue)
    return CircleGeomPlan(
        Transform(
            SpaceVector(*(Value * 1000 for Value in FrameValue.OriginValue)),
            SpaceVector(*FrameValue.AxisU),
            SpaceVector(*FrameValue.AxisV),
            SpaceVector(*FrameValue.NormalValue),
        ),
        CircleValue,
        Lower,
        Upper,
        {
            "method": "typed_parametric_offset_circular_boss",
            "model_version": 19000,
            "offset_owner": Driver.DepthValue.TypedOwner,
            "profile_owner": NativeNodeSpan(LinkValue, Profile),
            "radial_owner": SketchValue.dimensions[0].TypedOwner,
            "boss_owner": NativeNodeSpan(LinkValue, BossValue),
            "depth_owner": Depth.DepthValue.TypedOwner,
            "native_kernel_identity": False,
            "axial_interval_mm": (Lower, Upper),
        },
        BossValue,
    )
