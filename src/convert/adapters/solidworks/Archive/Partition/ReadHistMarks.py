from collections.abc import Mapping

from convert.Geometry.Parasolid import ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.CheckXmtMarks import CheckXmtMarks
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadRollbackMut import (
    ReadRollbackMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# selected active state must agree with the retained native marks and rollback ownership
def ReadHistMarks(
    DataValue: bytes, NodesValue: Mapping[int, XmtNode]
) -> tuple[int, int]:
    HeaderValue = ParaHeaderData(DataValue)
    if (
        HeaderValue is None
        or HeaderValue.schema != "SCH_3701250_37102_13006"
        or HeaderValue.description
        != ": TRANSMIT FILE (deltas) created by modeller version 3701250"
    ):
        raise ValueError("kernel history transmit profile is unqualified")
    CursorValue = XmtCursor(DataValue[HeaderValue.body_offset :])
    if CursorValue.ReadKind() != 3:
        raise ValueError("kernel history has no partition root")
    RootValue = ReadXmtNodeMut(CursorValue, 3)
    MarksValue: dict[int, XmtNode] = {}
    DeletedSets: dict[int, frozenset[int]] = {}
    while (KindValue := CursorValue.ReadKind()) != 1:
        if KindValue != 4 or len(MarksValue) >= 4096:
            raise ValueError("kernel history member is unqualified")
        MarkValue = ReadXmtNodeMut(CursorValue, 4)
        if MarkValue.IndexValue in MarksValue or MarkValue.IndexValue in NodesValue:
            raise ValueError("kernel mark identity is duplicated")
        MarksValue[MarkValue.IndexValue] = MarkValue
        if MarkValue.Integer("delta_key"):
            DeletedSets[MarkValue.IndexValue] = ReadRollbackMut(CursorValue, NodesValue)
    CursorValue.FinishRead()
    CheckXmtMarks(NodesValue, RootValue, MarksValue, DeletedSets)
    Current = MarksValue[RootValue.Integer("current_pmark")]
    PriorMark = MarksValue.get(Current.Integer("preceding"))
    return Current.Integer("id"), (
        PriorMark.Integer("id") if PriorMark is not None else 0
    )
