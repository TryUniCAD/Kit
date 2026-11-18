from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicGeom import (
    CheckPublicGeom,
)
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoots import (
    CheckPrismRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# strict reconstruction needs the complete linked grammar and whole model inventory before any shape can be inferred
def CheckPrismScope(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, ModelValue: NativeModel
) -> Mapping[int, ArchiveNode]:
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
        raise ValueError(
            "cache free prism requires complete nonprovisional native grammar"
        )
    if (
        ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or ModelValue.equations
    ):
        raise ValueError(
            "cache free prism has unsupported configuration or equation intent"
        )
    NodesValue = PrismNodes(LinkValue, ManagerValue)
    Features = IndexFeatures(LinkValue)
    CheckPrismRoots(Features, NodesValue)
    CheckPrismRoot(LinkValue.ConfigValue.RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPrismRels(LinkValue.ConfigValue.RootValue)
    CheckPublicGeom(ModelValue, Features)
    return Features
