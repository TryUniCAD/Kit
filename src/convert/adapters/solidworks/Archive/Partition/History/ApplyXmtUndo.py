from collections.abc import Mapping, Set
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.History.CheckUndoGraph import (
    CheckUndoGraph,
)
from convert.adapters.solidworks.Archive.Partition.History.XmtDelta import XmtDelta
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a previous state must replace only valid copies and restore genuinely absent slots
def ApplyXmtUndo(
    NodesValue: Mapping[int, XmtNode], DeltaValue: XmtDelta, Reserved: Set[int]
) -> Mapping[int, XmtNode]:
    Removed = dict(DeltaValue.RemovedValue)
    Restored = {
        NodeValue.IndexValue: NodeValue for NodeValue in DeltaValue.RestoredValue
    }
    Previous = {
        NodeValue.IndexValue: NodeValue for NodeValue in DeltaValue.PreviousValue
    }
    if (
        len(Removed) != len(DeltaValue.RemovedValue)
        or len(Restored) != len(DeltaValue.RestoredValue)
        or len(Previous) != len(DeltaValue.PreviousValue)
        or Removed.keys() & Previous.keys()
        or Restored.keys() & (NodesValue.keys() | Reserved)
        or 1 not in Previous
        or len(Previous) > DeltaValue.CopyCapacity
        or any(
            IndexValue not in NodesValue
            or NodesValue[IndexValue].KindValue != KindValue
            for IndexValue, KindValue in Removed.items()
        )
        or any(
            IndexValue not in NodesValue
            or NodesValue[IndexValue].KindValue != NodeValue.KindValue
            for IndexValue, NodeValue in Previous.items()
        )
    ):
        raise ValueError(
            "rollback slots overlap or disagree with the actual live owners"
        )
    ResultValue = {
        IndexValue: NodeValue
        for IndexValue, NodeValue in NodesValue.items()
        if IndexValue not in Removed
    }
    ResultValue.update(Restored)
    ResultValue.update(Previous)
    if len(ResultValue) > 4096:
        raise ValueError("rollback previous graph exceeds bounded size")
    CheckUndoGraph(ResultValue)
    return MappingProxyType(ResultValue)
