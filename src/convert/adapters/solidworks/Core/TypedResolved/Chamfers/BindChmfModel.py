from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.BindFeature import BindFeature
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.BindLineLoop import (
    BindLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReportTyped import ReportTyped


# the stock still uses its existing parametric extrusion and contour projection
def BindChmfModel(ModelValue: NativeModel, PartValue: ChmfPartRead) -> NativeModel:
    StockValue, LinkValue = PartValue.StockValue, PartValue.LinkValue
    Nodes = {NativeNodeId(Value): Value for Value in PartValue.RootsValue}
    Public = {Value.object_id: Value for Value in ModelValue.features}
    Features = {
        NativeId: BindFeature(Public[NativeId], Value, LinkValue)
        for NativeId, Value in Nodes.items()
    }
    StockId = NativeNodeId(StockValue.NodeValue)
    Features[StockId] = BindDepth(Features[StockId], StockValue)
    (SketchValue,) = ModelValue.sketches
    StockSketch = BindLineLoop(SketchValue, StockValue.ProfileValue, LinkValue)
    if StockSketch is None or StockSketch.TypedLines is None or StockSketch.dimensions:
        raise ValueError(
            "cold chamfer cannot project the whole actual free stock sketch"
        )
    StockOp, ChmfOp = ModelValue.operations
    Evidence = ReportTyped(
        ModelValue,
        LinkValue,
        Nodes,
        {StockId: StockValue},
        (),
        (SketchValue.object_id,),
    )
    PriorDiagnostic = ModelValue.TypedGraph.get("diagnostic")
    return ReplaceValue(
        ModelValue,
        features=tuple(Features.values()),
        operations=(BindExtrude(StockOp, StockValue), ChmfOp),
        sketches=(
            ReplaceValue(StockSketch, name=Features[SketchValue.object_id].name),
        ),
        planes=tuple(
            ReplaceValue(Plane, name=Features[Plane.object_id].name)
            for Plane in ModelValue.planes
        ),
        diagnostics=tuple(
            Message
            for Message in ModelValue.diagnostics
            if Message != f"typed resolved semantics unavailable: {PriorDiagnostic}"
        ),
        TypedGraph={
            **Evidence,
            "status": (
                "supplemented_cold_signed_chamfer"
                if PartValue.OwnersValue.ModeWord == 1
                else "supplemented_cold_distance_chamfer"
            ),
        },
    )
