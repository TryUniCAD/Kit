from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# tree replacement must preserve both root ownership and reciprocal parent links
def ReplaceSweepMut(
    StateValue: SweepState, NodeValue: SweepNode, Replacement: SweepNode | None
) -> None:
    if NodeValue.ParentValue is None:
        StateValue.RootValue = Replacement
    elif NodeValue.ParentValue.LeftValue is NodeValue:
        NodeValue.ParentValue.LeftValue = Replacement
    else:
        NodeValue.ParentValue.RightValue = Replacement
    if Replacement is not None:
        Replacement.ParentValue = NodeValue.ParentValue
