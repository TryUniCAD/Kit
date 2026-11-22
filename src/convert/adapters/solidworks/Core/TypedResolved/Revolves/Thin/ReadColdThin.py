from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.BindColdSketch import (
    BindColdSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.ColdRevolve import (
    ColdRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BuildThinGeom import (
    BuildThinGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinOwner import (
    ReadThinOwner,
)


# rebuilds from editable intent bind the actual public sketch and native features
def ReadColdThin(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> tuple[NativeModel, ColdRevolve]:
    CheckGeometry(LinkValue, ManagerValue, ModelValue)
    OwnerValue = ReadThinOwner(LinkValue, ManagerValue)
    SweepValue = OwnerValue.SweepValue
    Features = IndexFeatures(LinkValue)
    ProfileId = NativeNodeId(SweepValue.ProfileValue)
    FeatureId = NativeNodeId(SweepValue.NodeValue)
    (SketchValue,) = ModelValue.sketches
    if (
        ModelValue.operations
        or len(ModelValue.features) != len(Features)
        or {Value.object_id for Value in ModelValue.features} != set(Features)
        or SketchValue.object_id != ProfileId
        or not any(
            FeatureValue.object_id == FeatureId
            and FeatureValue.kind == "Revolve-Thin"
            and FeatureValue.class_name == "moRevolutionThin_c"
            for FeatureValue in ModelValue.features
        )
    ):
        raise ValueError("SOLIDWORKS thin cold geometry lacks its public owner links")
    CheckPlanes(ModelValue, Features)
    Bound = BindColdSketch(ModelValue, SweepValue)
    return Bound, ColdRevolve(LinkValue, OwnerValue, BuildThinGeom(OwnerValue, BodyId))
