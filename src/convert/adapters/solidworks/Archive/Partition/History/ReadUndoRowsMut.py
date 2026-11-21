from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Partition.History.ReadXmtQualMut import (
    ReadXmtQualMut,
)
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# previous records use the current field schema and their own null terminated sequence
def ReadUndoRowsMut(
    CursorValue: XmtCursor, Qualifiers: dict[int, bool], RowLimit: int
) -> tuple[XmtNode, ...]:
    RowsValue: list[XmtNode] = []
    ValueReader = PartialValue(ReadXmtQualMut, Qualifiers=Qualifiers)
    while (KindValue := CursorValue.ReadKind()) != 1:
        if KindValue in (3, 4) or KindValue not in KKernelShapes:
            raise ValueError("unqualified rollback row class or count")
        if len(RowsValue) >= RowLimit:
            raise ValueError("rollback rows exceed their bounded capacity")
        RowsValue.append(
            ReadXmtNodeMut(CursorValue, KindValue, ValueReader=ValueReader)
        )
    if CursorValue.ReadIndex():
        raise ValueError("rollback row sequence lacks its null terminator")
    return tuple(RowsValue)
