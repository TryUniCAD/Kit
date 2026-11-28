from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)


# broken internal tree links must fail explicitly instead of weakening polygon validation
def NeedSweepNode(NodeValue: SweepNode | None) -> SweepNode:
    if NodeValue is None:
        raise ValueError("polygon sweep tree has an invalid child")
    return NodeValue
