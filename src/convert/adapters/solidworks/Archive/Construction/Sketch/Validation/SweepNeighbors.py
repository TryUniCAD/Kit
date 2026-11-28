from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# predecessor lookup identifies the only lower neighbor introduced by insertion or removal
def BeforeSweep(NodeValue: SweepNode) -> SweepNode | None:
    if NodeValue.LeftValue is not None:
        NodeValue = NodeValue.LeftValue
        while NodeValue.RightValue is not None:
            NodeValue = NodeValue.RightValue
        return NodeValue
    while (
        NodeValue.ParentValue is not None
        and NodeValue.ParentValue.LeftValue is NodeValue
    ):
        NodeValue = NodeValue.ParentValue
    return NodeValue.ParentValue


# successor lookup identifies upper neighbors and exact vertical range members
def AfterSweep(NodeValue: SweepNode) -> SweepNode | None:
    if NodeValue.RightValue is not None:
        NodeValue = NodeValue.RightValue
        while NodeValue.LeftValue is not None:
            NodeValue = NodeValue.LeftValue
        return NodeValue
    while (
        NodeValue.ParentValue is not None
        and NodeValue.ParentValue.RightValue is NodeValue
    ):
        NodeValue = NodeValue.ParentValue
    return NodeValue.ParentValue


# vertical edges need the first active ordinate in their closed coordinate range
def LowerSweep(StateValue: SweepState, Ordinate: Fraction) -> SweepNode | None:
    NodeValue = StateValue.RootValue
    FoundValue: SweepNode | None = None
    while NodeValue is not None:
        if NodeValue.EdgeValue.GetOrdinate(StateValue.PositionX) >= Ordinate:
            FoundValue = NodeValue
            NodeValue = NodeValue.LeftValue
        else:
            NodeValue = NodeValue.RightValue
    return FoundValue
