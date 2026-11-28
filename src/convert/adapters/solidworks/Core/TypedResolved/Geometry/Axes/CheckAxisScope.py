from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.CheckAxisMap import (
    CheckAxisMap,
    KAxisClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import (
    KPrismClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# only complete linked stocks with their exclusive axis members permit analytic reconstruction
def CheckAxisScope(
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ModelValue: NativeModel,
    Features: Mapping[int, ArchiveNode],
    ColdValue: ColdOutput,
    AxesValue: PrismAxes,
) -> None:
    if (
        ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or ModelValue.equations
    ):
        raise ValueError(
            "cache free box has unsupported configuration or equation state"
        )
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
            ManagerValue.ReportValue,
        )
    ):
        raise ValueError(
            "cache free box requires complete nonprovisional native grammar"
        )
    NodesValue = PrismNodes(
        LinkValue,
        ManagerValue,
        ColdValue.AtomValue,
        AllowedClasses=KPrismClasses | KAxisClasses,
    )
    CheckPrismRoots(*CheckAxisMap(LinkValue, Features, NodesValue, AxesValue))
    RootValue = LinkValue.ConfigValue.RootValue
    CheckPrismRoot(RootValue, 1)
    CheckPrismRels(RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPlanes(ModelValue, Features)
