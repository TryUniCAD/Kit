from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleClasses import (
    KCircleClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# inferred geometry requires its full classified part configuration and native owner inventory
def CheckColdCirc(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    Features: Mapping[int, ArchiveNode],
) -> None:
    Reports = (
        LinkValue.ConfigValue.ReportValue,
        LinkValue.ResolvedValue.ReportValue,
        ManagerValue.ReportValue,
    )
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in Reports
    ):
        raise ValueError("cold circle requires the complete linked archive grammar")
    if (
        ModelValue.equations
        or len(ModelValue.configurations) != 1
        or len(ModelValue.features) != len(Features)
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
    ):
        raise ValueError("cold circle has unresolved configuration or feature owners")
    NodesValue = PrismNodes(LinkValue, ManagerValue, AllowedClasses=KCircleClasses)
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
    RootValue = LinkValue.ConfigValue.RootValue
    CheckPrismRoot(RootValue)
    CheckPrismRels(RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPrismPlane(Features, RootValue)
    CheckPlanes(ModelValue, Features)
