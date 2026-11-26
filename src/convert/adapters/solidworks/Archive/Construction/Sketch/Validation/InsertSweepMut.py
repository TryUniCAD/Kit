from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.BalanceSweepMut import (
    BalanceSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.EdgeOrder import (
    SweepEdgeKey,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# insertion must expose the exact neighboring edges before any later event can hide a crossing
def InsertSweepMut(StateValue: SweepState, EdgeValue: SweepEdge) -> SweepNode:
    NodeValue = SweepNode(EdgeValue)
    if StateValue.RootValue is None:
        StateValue.RootValue = NodeValue
    else:
        ParentValue = StateValue.RootValue
        KeyValue = SweepEdgeKey(StateValue, EdgeValue)
        while True:
            IsLeft = KeyValue < SweepEdgeKey(StateValue, ParentValue.EdgeValue)
            ChildValue = ParentValue.LeftValue if IsLeft else ParentValue.RightValue
            if ChildValue is None:
                NodeValue.ParentValue = ParentValue
                if IsLeft:
                    ParentValue.LeftValue = NodeValue
                else:
                    ParentValue.RightValue = NodeValue
                break
            ParentValue = ChildValue
        BalanceSweepMut(StateValue, ParentValue)
    StateValue.NodesValue[EdgeValue.IndexValue] = NodeValue
    return NodeValue
