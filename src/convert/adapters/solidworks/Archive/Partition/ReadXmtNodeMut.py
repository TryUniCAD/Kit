from collections.abc import Callable

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadXmtShapeMut import (
    ReadXmtShapeMut,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# whole record decoding prevents body names from being found by incidental byte patterns
def ReadXmtNodeMut(
    CursorValue: XmtCursor,
    KindValue: int,
    PreviousWorld: bool = False,
    *,
    ValueReader: Callable[[XmtCursor, XmtField, bool], object] = ReadXmtValueMut,
) -> XmtNode:
    if KindValue not in KKernelShapes:
        raise ValueError("kernel class is outside the mapped current schema")
    return ReadXmtShapeMut(
        CursorValue,
        KindValue,
        KKernelShapes[KindValue],
        PreviousWorld,
        ValueReader=ValueReader,
    )
