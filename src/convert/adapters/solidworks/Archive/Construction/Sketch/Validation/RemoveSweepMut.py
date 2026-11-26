from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.BalanceSweepMut import (
    BalanceSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.NeedSweepNode import (
    NeedSweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReplaceSweepMut import (
    ReplaceSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNeighbors import (
    AfterSweep,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# ended edges must leave the same identity index and balanced active ordering
def RemoveSweepMut(StateValue: SweepState, IndexValue: int) -> None:
    NodeValue = StateValue.NodesValue.pop(IndexValue)
    if NodeValue.LeftValue is not None and NodeValue.RightValue is not None:
        FollowingValue = NeedSweepNode(AfterSweep(NodeValue))
        NodeValue.EdgeValue, FollowingValue.EdgeValue = (
            FollowingValue.EdgeValue,
            NodeValue.EdgeValue,
        )
        StateValue.NodesValue[NodeValue.EdgeValue.IndexValue] = NodeValue
        NodeValue = FollowingValue
    ParentValue = NodeValue.ParentValue
    ReplaceSweepMut(
        StateValue,
        NodeValue,
        (
            NodeValue.LeftValue
            if NodeValue.LeftValue is not None
            else NodeValue.RightValue
        ),
    )
    BalanceSweepMut(StateValue, ParentValue)
