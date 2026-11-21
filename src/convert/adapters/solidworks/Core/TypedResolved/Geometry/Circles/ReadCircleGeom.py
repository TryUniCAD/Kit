from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.BuildCircGeom import (
    BuildCircGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleClasses import (
    KCircleClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.ReadCircPlan import (
    ReadCircPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# one ordinary circle boss qualifies only with complete grammar roots configuration and actual scalar and profile owners
def ReadCircleGeom(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> PartGeometry:
    CheckGeometry(LinkValue, ManagerValue, ModelValue)
    NodesValue = PrismNodes(LinkValue, ManagerValue, AllowedClasses=KCircleClasses)
    Features = IndexFeatures(LinkValue)
    CheckPrismRoots(
        Features,
        NodesValue,
        RequiredClasses=(
            "moEndSpec_c",
            "moFromEndSpec_c",
            "moDisplayRadialDim_c",
            "moSkDimHandleRadial_c",
            "sgCircleDim",
        ),
    )
    CheckPrismRoot(LinkValue.ConfigValue.RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPrismRels(LinkValue.ConfigValue.RootValue)
    return BuildCircGeom(ReadCircPlan(LinkValue, Features, ModelValue), BodyId)
