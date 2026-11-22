from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ProjectEllip import (
    ProjectEllip,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ReadEllipRows import (
    ReadEllipHandle,
    ReadEllipRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckFirstBoss,
    CheckPrismBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoots import (
    CheckPrismRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import (
    KPrismClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform

# the typed ellipse branch adds only its one owning conic handle to the ordinary blind part inventory
KEllipClasses = KPrismClasses | frozenset(("sgEllipseHandle",))


# one ordinary compressed ellipse cannot carry alternate part body or configuration state
def CheckEllipPart(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    ModelValue: NativeModel,
) -> None:
    Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
    CheckGeometry(LinkValue, Manager, ModelValue)
    Nodes = PrismNodes(LinkValue, Manager, AllowedClasses=KEllipClasses)
    Features = IndexFeatures(LinkValue)
    CheckPrismRoots(
        Features,
        Nodes,
        RequiredClasses=("moEndSpec_c", "moFromEndSpec_c", "sgEllipseHandle"),
    )
    CheckPrismRoot(LinkValue.ConfigValue.RootValue)
    CheckPrismRels(LinkValue.ConfigValue.RootValue)
    CheckPrismMgr(Manager, CompressedValue=1)
    if LinkValue.ResolvedValue.ContextValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise ValueError("ellipse has an unsupported linked part context")
    if LinkValue.ResolvedValue.ExtraFields != {"n": 0, "fcd8": []} or set(Features) != {
        Value.object_id for Value in ModelValue.features
    }:
        raise ValueError("ellipse has extra body or unprojected feature ownership")
    CheckPlanes(ModelValue, Features)


# one scope proof must join the exact stock sketch and live depth before neutral publication
def ReadEllipPart(Archive: SldprtArchive, ModelValue: NativeModel) -> EllipPartRead:
    LinkValue = ReadNativeLink(Archive, 0, ReadEllipses=True)
    CheckEllipPart(Archive, LinkValue, ModelValue)
    Features = IndexFeatures(LinkValue)
    BossNode = RequireNative(LinkValue.ResolvedValue.RootsValue[-1], "moExtrusion_c")
    OwnerValue = ReadExtrude(LinkValue, BossNode, Features)
    CheckFirstBoss(OwnerValue)
    CheckPrismBoss(OwnerValue)
    CheckPrismEnd(OwnerValue)
    Profile = OwnerValue.ProfileValue
    CheckPrismProf(Profile)
    RootValue = LinkValue.ConfigValue.RootValue
    CheckPrismPlane(Features, RootValue)
    FrameValue = ReadPrismFrame(Profile, RootValue, Features)
    RefValue = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    (Sketch,) = ModelValue.sketches
    (Operation,) = ModelValue.operations
    Driver = OwnerValue.RequireDepth().DepthValue
    if (
        FrameValue != Transform()
        or NativeNodeId(Profile) != Sketch.object_id
        or Sketch.support_plane_id
        != NativeRecord(RefValue.FieldsValue.get("ff0")).get("f00")
        or NativeNodeId(BossNode) != Operation.object_id
        or Operation.profile_id != Sketch.object_id
        or Driver.name != "D1"
        or Driver.native_role != "driving"
        or Driver.native_value is None
    ):
        raise ValueError("ellipse has unresolved sketch support or driving depth")
    SketchValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    SegmentId, Points = ReadEllipRows(SketchValue)
    Handle, PointIds = ReadEllipHandle(Points)
    CheckTreeAlias(LinkValue, (Profile, BossNode, SketchValue, Handle))
    Geometry, Stations = ProjectEllip(Points, Driver.native_value)
    return EllipPartRead(
        LinkValue,
        OwnerValue,
        SketchValue,
        Handle,
        Geometry,
        Stations,
        SegmentId,
        PointIds,
    )


# the diagnostic is only a dispatch hint while the full alternate archive must validate independently
def TryEllipPart(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    Settings: ReadOptions,
) -> EllipPartRead | None:
    if (
        Settings.extract_raw_brep
        or ModelValue.TypedGraph.get("diagnostic")
        != "unsupported SOLIDWORKS body class sgEllipseHandle schema 1"
        or tuple(
            (Value.configuration_id, Value.name) for Value in ModelValue.configurations
        )
        != ((0, "Default"),)
        or len(ModelValue.sketches) != 1
        or tuple(Value.kind for Value in ModelValue.operations) != ("join",)
        or not IsCacheAbsent(Archive)
    ):
        return None
    try:
        return ReadEllipPart(Archive, ModelValue)
    except (ValueError, TypeError, KeyError, OverflowError):
        return None
