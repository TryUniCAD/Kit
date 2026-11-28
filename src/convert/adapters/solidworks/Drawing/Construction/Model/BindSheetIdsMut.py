from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetGraph import SheetGraph


# the measured sheet reservation must bind its actual constructed objects into the surrounding document allocator
def BindSheetIdsMut(GraphValue: SheetGraph, Allocator: PersistentIds) -> None:
    NodesValue = (
        GraphValue.SheetValue,
        GraphValue.PlaneValue,
        GraphValue.ProfileValue,
        GraphValue.DetailValue,
    )
    ExpectedValue = tuple(
        range(Allocator.NextValue, Allocator.NextValue + len(NodesValue))
    )
    if (
        Allocator.ReservedSet
        or tuple(NodeValue.FieldsValue["f08"] for NodeValue in NodesValue)
        != ExpectedValue
    ):
        raise ValueError(
            "drawing root sheet reservation differs from actual allocation order"
        )
    for NodeValue, Identifier in zip(NodesValue, ExpectedValue, strict=True):
        NodeValue.FieldsValue["f08"] = -1
        if Allocator.AllocateMut(NodeValue) != Identifier:
            raise ValueError(
                "drawing root sheet registration changed its generated identity"
            )
    if Allocator.NextValue != GraphValue.NextIdValue:
        raise ValueError("drawing root sheet allocator boundary differs")
