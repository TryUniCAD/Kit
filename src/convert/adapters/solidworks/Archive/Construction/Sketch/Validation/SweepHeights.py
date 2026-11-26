from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)


# empty subtrees need one height convention for deterministic balancing
def SweepHeight(NodeValue: SweepNode | None) -> int:
    return 0 if NodeValue is None else NodeValue.HeightValue


# balance updates must reflect current child links after every tree mutation
def RefreshSweepMut(NodeValue: SweepNode) -> None:
    NodeValue.HeightValue = 1 + max(
        SweepHeight(NodeValue.LeftValue), SweepHeight(NodeValue.RightValue)
    )
