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
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the edge modifier projection must keep its actual earlier boss and complete neutral datum reference
def BindChmfModel(ModelValue: NativeModel, PartValue: ChmfPartRead) -> NativeModel:
    StockValue, LinkValue = PartValue.StockValue, PartValue.LinkValue
    Public = {Value.object_id: Value for Value in ModelValue.features}
    Features = {
        NativeNodeId(Value): BindFeature(Public[NativeNodeId(Value)], Value, LinkValue)
        for Value in PartValue.RootsValue
    }
    StockId = NativeNodeId(StockValue.NodeValue)
    Features[StockId] = BindDepth(Features[StockId], StockValue)
    (SketchValue,) = ModelValue.sketches
    Reference = RequireNative(StockValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int or not any(Value.object_id == PlaneId for Value in ModelValue.planes):
        raise ValueError("cold chamfer stock lacks its actual public Front datum")
    SketchValue = ReplaceValue(SketchValue, support_plane_id=PlaneId)
    StockSketch = BindLineLoop(SketchValue, StockValue.ProfileValue, LinkValue)
    if StockSketch is None or StockSketch.TypedLines is None or StockSketch.dimensions:
        raise ValueError("cold chamfer cannot project the actual free stock sketch")
    StockOp, ChmfOp = ModelValue.operations
    return ReplaceValue(
        ModelValue,
        features=tuple(Features.values()),
        operations=(BindExtrude(StockOp, StockValue), ChmfOp),
        sketches=(ReplaceValue(StockSketch, name=Features[SketchValue.object_id].name),),
        planes=tuple(
            ReplaceValue(Plane, name=Features[Plane.object_id].name)
            for Plane in ModelValue.planes
        ),
    )
