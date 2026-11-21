from collections.abc import Mapping
from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Partition.CheckXmtMarks import CheckXmtMarks
from convert.adapters.solidworks.Archive.Partition.History.ReadHistFrames import (
    ReadHistFrames,
)
from convert.adapters.solidworks.Archive.Partition.ReadRollbackMut import (
    ReadRollbackMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# selected active state must agree with the retained native marks and rollback ownership
def ReadHistMarks(
    DataValue: bytes, NodesValue: Mapping[int, XmtNode]
) -> tuple[int, int]:
    ReadDelta = PartialValue(ReadRollbackMut, NodesValue=NodesValue)
    RootValue, MarksValue, DeletedSets = ReadHistFrames(DataValue, NodesValue, ReadDelta)
    CheckXmtMarks(NodesValue, RootValue, MarksValue, DeletedSets)
    Current = MarksValue[RootValue.Integer("current_pmark")]
    PriorMark = MarksValue.get(Current.Integer("preceding"))
    return Current.Integer("id"), (
        PriorMark.Integer("id") if PriorMark is not None else 0
    )
