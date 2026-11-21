from collections.abc import Callable, Mapping
from typing import TypeVar

from convert.Geometry.Parasolid import ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# the mark envelope must preserve the result type of its selected rollback grammar
KDeltaType = TypeVar("KDeltaType")


# both history profiles need the same trusted mark framing and transmit index boundary
def ReadHistFrames(
    DataValue: bytes,
    NodesValue: Mapping[int, XmtNode],
    ReadDelta: Callable[[XmtCursor], KDeltaType],
    *,
    MarkLimit: int = 4096,
) -> tuple[XmtNode, dict[int, XmtNode], dict[int, KDeltaType]]:
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
    DeltasValue: dict[int, KDeltaType] = {}
    while (KindValue := CursorValue.ReadKind()) != 1:
        if KindValue != 4 or len(MarksValue) >= MarkLimit:
            raise ValueError("kernel history member is unqualified")
        MarkValue = ReadXmtNodeMut(CursorValue, 4)
        if MarkValue.IndexValue in MarksValue or MarkValue.IndexValue in NodesValue:
            raise ValueError("kernel mark identity is duplicated")
        MarksValue[MarkValue.IndexValue] = MarkValue
        if MarkValue.Integer("delta_key"):
            DeltasValue[MarkValue.IndexValue] = ReadDelta(CursorValue)
    CursorValue.FinishRead()
    return RootValue, MarksValue, DeltasValue
