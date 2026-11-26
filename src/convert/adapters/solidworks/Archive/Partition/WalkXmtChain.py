from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# reciprocal native chains distinguish active owned records from detached matching labels
def WalkXmtChain(
    NodesValue: Mapping[int, XmtNode],
    IndexValue: int,
    KindValue: int,
    NextField: str = "next",
    PreviousField: str | None = "previous",
    OwnerField: str | None = None,
    OwnerValue: int | None = None,
) -> tuple[int, ...]:
    ResultValue: list[int] = []
    SeenValue: set[int] = set()
    Previous = 0
    while IndexValue:
        if IndexValue in SeenValue:
            raise ValueError("kernel owner chain is cyclic")
        NodeValue = RequireXmt(NodesValue, IndexValue, KindValue)
        if (
            PreviousField is not None
            and NodeValue.Integer(PreviousField) != Previous
            or OwnerField is not None
            and NodeValue.Integer(OwnerField) != OwnerValue
        ):
            raise ValueError("kernel owner chain is not reciprocal")
        SeenValue.add(IndexValue)
        ResultValue.append(IndexValue)
        Previous, IndexValue = IndexValue, NodeValue.Integer(NextField)
    return tuple(ResultValue)
