from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.BuildPocketGeom import (
    BuildPocketGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckPublicPocket import (
    CheckPublicPocket,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismGeometry import (
    PrismGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import (
    ReadPrismPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan


# body geometry and history must refer to the same native owners before a cache free document can supply a pocket solid
def ReadPocketGeom(
    LinkValue: NativeLink, Manager: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> PrismGeometry:
    Report = Manager.ReportValue
    if (
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
    ):
        raise ValueError(
            "cache free pocket requires complete configuration manager grammar"
        )
    CheckPrismMgr(Manager)
    Features = IndexFeatures(LinkValue)
    CircleValue, CutDepth = CheckPublicPocket(ModelValue, Features)
    Stock = ReadPrismPlan(LinkValue, Features)
    CutNode = Features[ModelValue.operations[1].object_id]
    PlanValue = ReplaceValue(
        Stock,
        EvidenceValue={
            **Stock.EvidenceValue,
            "method": "typed_parametric_blind_circular_pocket",
            "cut_owner": NativeNodeSpan(LinkValue, CutNode),
            "cut_circle_owner": CircleValue.OwnerValue,
            "cut_depth_mm": CutDepth,
        },
    )
    return BuildPocketGeom(PlanValue, CircleValue, CutDepth, BodyId)
