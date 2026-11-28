from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# runtime marks count hidden pointer value nodes for the entities allocated in that transition
def CountRollNodes(
    NodesValue: tuple[XmtNode, ...],
    GraphValue: Mapping[int, XmtNode],
    PointerSlots: Mapping[int, tuple[int, ...]],
) -> int:
    Owners = {NodeValue.IndexValue: NodeValue for NodeValue in NodesValue}
    if len(Owners) != len(NodesValue) or any(
        GraphValue.get(IndexValue) is not NodeValue
        for IndexValue, NodeValue in Owners.items()
    ):
        raise ValueError(
            "SOLIDWORKS rollback allocations repeat or detach a transmit slot"
        )
    CountValue = len(Owners)
    for IndexValue, Positions in PointerSlots.items():
        OwnerValue = RequireXmt(Owners, IndexValue, 81)
        FieldsValue = OwnerValue.Indexes("fields")
        KindsValue = RequireXmt(
            GraphValue, OwnerValue.Integer("definition"), 80
        ).Indexes("fields")
        if (
            len(FieldsValue) != len(KindsValue)
            or not Positions
            or len(set(Positions)) != len(Positions)
            or any(
                not 0 <= Position < len(FieldsValue)
                or FieldsValue[Position] != 0
                or KindsValue[Position] != 9
                for Position in Positions
            )
        ):
            raise ValueError("SOLIDWORKS rollback has unbound hidden pointer slots")
        CountValue += len(Positions)
    return CountValue
