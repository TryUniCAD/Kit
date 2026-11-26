from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.NeedSweepNode import (
    NeedSweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RotateSweepMut import (
    RotateSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepHeights import (
    RefreshSweepMut,
    SweepHeight,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# bounded tree height keeps simple polygon validation scalable for independent model sizes
def BalanceSweepMut(StateValue: SweepState, NodeValue: SweepNode | None) -> None:
    while NodeValue is not None:
        RefreshSweepMut(NodeValue)
        BalanceValue = SweepHeight(NodeValue.LeftValue) - SweepHeight(
            NodeValue.RightValue
        )
        if BalanceValue > 1:
            ChildValue = NeedSweepNode(NodeValue.LeftValue)
            if SweepHeight(ChildValue.LeftValue) < SweepHeight(ChildValue.RightValue):
                _ = RotateSweepMut(StateValue, ChildValue, True)
            NodeValue = RotateSweepMut(StateValue, NodeValue, False)
        elif BalanceValue < -1:
            ChildValue = NeedSweepNode(NodeValue.RightValue)
            if SweepHeight(ChildValue.RightValue) < SweepHeight(ChildValue.LeftValue):
                _ = RotateSweepMut(StateValue, ChildValue, False)
            NodeValue = RotateSweepMut(StateValue, NodeValue, True)
        NodeValue = NodeValue.ParentValue
