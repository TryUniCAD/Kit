from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BuildThinGeom import (
    BuildThinGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinOwner import (
    ReadThinOwner,
)


# rebuilds from editable intent bind the actual public sketch and native features
def ReadThinGeom(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> PartGeometry:
    CheckGeometry(LinkValue, ManagerValue, ModelValue)
    OwnerValue = ReadThinOwner(LinkValue, ManagerValue)
    SweepValue = OwnerValue.SweepValue
    Features = IndexFeatures(LinkValue)
    Reference = RequireNative(
        SweepValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    (SketchValue,) = ModelValue.sketches
    if (
        ModelValue.TypedGraph.get("status") != "supplemented"
        or len(ModelValue.features) != len(Features)
        or {Value.object_id for Value in ModelValue.features} != set(Features)
        or SketchValue.object_id != NativeNodeId(SweepValue.ProfileValue)
        or SketchValue.support_plane_id != PlaneId
    ):
        raise ValueError("SOLIDWORKS thin cold geometry lacks its public owner links")
    CheckPlanes(ModelValue, Features)
    return BuildThinGeom(OwnerValue, BodyId)
