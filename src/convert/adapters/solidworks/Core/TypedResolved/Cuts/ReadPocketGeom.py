from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.BuildCircularCut import (
    BuildCircularCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckPublicPocket import (
    CheckPublicPocket,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import (
    ReadPrismPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Features.FeatureExtrude import ExtrudeEnd


# body geometry and history must refer to the same native owners before a cache free document can supply a pocket solid
def ReadPocketGeom(
    LinkValue: NativeLink, Manager: CmgrGraph, ModelValue: NativeModel, BodyId: str
) -> PartGeometry:
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
    CircleValue, Cut = CheckPublicPocket(ModelValue, Features)
    Through = Cut.extrusion_end == ExtrudeEnd.KThroughAll
    Evidence = NativeRecord(ModelValue.TypedGraph.get("cut_body_dependency"))
    Stock = ReadPrismPlan(
        LinkValue,
        Features,
        ModeValue=ExtrudeEnd.KMidPlane if Through else ExtrudeEnd.KBlind,
        SelectedStock=Evidence.get("binding") == "cold_selected_stock_atom",
    )
    if Through:
        HalfDepth = Stock.DepthValue * 0.5
        StockBounds = (-HalfDepth, HalfDepth)
        if Cut.second_extrusion_end == ExtrudeEnd.KThroughAll:
            CutBounds = StockBounds
        elif Cut.direction_code == 1:
            CutBounds = (0.0, HalfDepth)
        else:
            CutBounds = (-HalfDepth, 0.0)
        MethodValue = "typed_parametric_through_all_circular_cut"
        CutEvidence: dict[str, object] = {
            "stock_interval_mm": StockBounds,
            "cut_interval_mm": CutBounds,
        }
        PrefixValue = f"{BodyId}-through-all-cut"
    else:
        if Cut.length_mm is None:
            raise ValueError("cache free blind cut requires an active length")
        StockBounds, CutBounds = (0.0, Stock.DepthValue), (0.0, Cut.length_mm)
        MethodValue = "typed_parametric_blind_circular_pocket"
        CutEvidence = {"cut_depth_mm": Cut.length_mm}
        PrefixValue = f"{BodyId}-blind-pocket"
    CutNode = Features[Cut.object_id]
    PlanValue = ReplaceValue(
        Stock,
        EvidenceValue={
            **Stock.EvidenceValue,
            "method": MethodValue,
            "cut_owner": NativeNodeSpan(LinkValue, CutNode),
            "cut_circle_owner": CircleValue.OwnerValue,
            **CutEvidence,
        },
    )
    return BuildCircularCut(
        PlanValue, CircleValue, StockBounds, CutBounds, BodyId, PrefixValue
    )
