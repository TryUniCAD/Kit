from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import (
    KPrismClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.BuildRevBodyGeom import (
    BuildRevBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.CheckRevAngles import (
    CheckRevAngles,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)

# the ordinary cold revolve reuses the standard system graph and owns its own angular end and selected line
KRevolveGeomClasses = KPrismClasses - {
    "moExtrusion_c",
    "moEndSpec_c",
    "moFromEndSpec_c",
} | {"moRevolution_c", "moRevEndSpec_c", "moLineRef_w"}


# require complete native and public ownership before producing a solid from an absent cache
def ReadRevGeom(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> PartGeometry:
    CheckGeometry(LinkValue, ManagerValue, ModelValue)
    Features = IndexFeatures(LinkValue)
    Nodes = PrismNodes(LinkValue, ManagerValue, AllowedClasses=KRevolveGeomClasses)
    CheckPrismRoots(
        Features,
        Nodes,
        SolidClass="moRevolution_c",
        RequiredClasses=(
            "moRevEndSpec_c",
            "moLineRef_w",
            "moCompSketchEntHandle_c",
        ),
    )
    CheckPrismRoot(LinkValue.ConfigValue.RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPrismRels(LinkValue.ConfigValue.RootValue)
    (OwnerValue,) = ReadRevOwners(LinkValue)
    CheckRevAngles(Nodes, OwnerValue.EndValue)
    CheckPrismAtom(OwnerValue.NodeValue)
    if (
        ModelValue.TypedGraph.get("status") != "supplemented"
        or len(ModelValue.features) != len(Features)
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
        or len(ModelValue.operations) != 1
        or len(ModelValue.sketches) != 1
    ):
        raise ValueError("cache free revolve lacks complete public feature ownership")
    Operation = ModelValue.operations[0]
    ReferenceValue = RequireNative(
        OwnerValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    PlaneId = NativeRecord(ReferenceValue.FieldsValue.get("ff0")).get("f00")
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    SketchValue = ModelValue.sketches[0]
    if (
        Operation.kind != "revolve_join"
        or Operation.object_id != NativeNodeId(OwnerValue.NodeValue)
        or Operation.profile_id != ProfileId
        or SketchValue.object_id != ProfileId
        or SketchValue.support_plane_id != PlaneId
    ):
        raise ValueError("cache free revolve public operation or support differs")
    CheckPlanes(ModelValue, Features)
    return BuildRevBody(OwnerValue, BodyId)
