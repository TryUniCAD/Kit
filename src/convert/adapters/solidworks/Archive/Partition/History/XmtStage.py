from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.History.XmtDelta import XmtDelta
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# each selected mark must retain its own immutable predecessor transaction context
@DataClass(frozen=True, slots=True)
class XmtStage:
    MarkValue: XmtNode
    NodesValue: Mapping[int, XmtNode]
    UndoValue: XmtDelta | None
