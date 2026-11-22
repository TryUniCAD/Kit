from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import (
    KRefSupportSource,
    NativeModel,
    NativeProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisStock import (
    AxisStock,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineNativeDims import (
    LineNativeDims,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# public history and the analytic boundary must agree on every linked native identity
def BindAxisStock(
    ModelValue: NativeModel, StockValue: AxisStock, Features: Mapping[int, ArchiveNode]
) -> NativeModel:
    (Operation,) = ModelValue.operations
    (SketchValue,) = ModelValue.sketches
    OwnerValue = StockValue.OwnerValue
    BossId = NativeNodeId(OwnerValue.NodeValue)
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    Inventory = {Feature.object_id: Feature for Feature in ModelValue.features}
    if (
        len(Inventory) != len(ModelValue.features)
        or Inventory.keys() != Features.keys()
        or any(
            Inventory[KeyValue].name != ReadNativeName(NodeValue)
            for KeyValue, NodeValue in Features.items()
        )
        or Operation.kind != "join"
        or Operation.object_id != BossId
        or Operation.profile_id != ProfileId
        or SketchValue.object_id != ProfileId
    ):
        raise ValueError(
            "cache free box lacks its complete indexed feature and sketch owners"
        )
    LoopValue = StockValue.LoopValue
    Dimensions = LineNativeDims(LoopValue.DimsValue)
    Sketch = ReplaceValue(
        SketchValue,
        support_plane_id=StockValue.PlaneId,
        support_source=KRefSupportSource,
        unframed_support_plane_id=None,
        support_plane=None,
        TypedFrame=StockValue.FrameValue,
        TypedLines=LoopValue,
        profiles=(
            NativeProfile(
                "line-loop",
                tuple(
                    Coordinate
                    for Point in LoopValue.PointsValue
                    for Coordinate in Point.PositionValue
                ),
                (),
            ),
        ),
        dimensions=Dimensions,
        constraints=(),
    )
    BoundFeatures = tuple(
        (
            BindDepth(Inventory[KeyValue], OwnerValue)
            if KeyValue == BossId
            else (
                ReplaceValue(Inventory[KeyValue], dimensions=Dimensions)
                if KeyValue == ProfileId
                else Inventory[KeyValue]
            )
        )
        for KeyValue in Features
    )
    return ReplaceValue(
        ModelValue,
        features=BoundFeatures,
        sketches=(Sketch,),
        operations=(BindExtrude(Operation, OwnerValue),),
    )
