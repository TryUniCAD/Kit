from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.NeedSweepNode import (
    NeedSweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReplaceSweepMut import (
    ReplaceSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepHeights import (
    RefreshSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# exact sweep ordering needs balanced links without changing edge identities
def RotateSweepMut(
    StateValue: SweepState, NodeValue: SweepNode, IsLeft: bool
) -> SweepNode:
    PivotValue = NeedSweepNode(NodeValue.RightValue if IsLeft else NodeValue.LeftValue)
    ReplaceSweepMut(StateValue, NodeValue, PivotValue)
    MiddleValue = PivotValue.LeftValue if IsLeft else PivotValue.RightValue
    if IsLeft:
        NodeValue.RightValue = MiddleValue
        PivotValue.LeftValue = NodeValue
    else:
        NodeValue.LeftValue = MiddleValue
        PivotValue.RightValue = NodeValue
    if MiddleValue is not None:
        MiddleValue.ParentValue = NodeValue
    NodeValue.ParentValue = PivotValue
    RefreshSweepMut(NodeValue)
    RefreshSweepMut(PivotValue)
    return PivotValue
