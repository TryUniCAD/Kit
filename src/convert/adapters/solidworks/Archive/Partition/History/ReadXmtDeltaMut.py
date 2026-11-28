from struct import unpack as UnpackValue
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.History.ReadUndoRowsMut import (
    ReadUndoRowsMut,
)
from convert.adapters.solidworks.Archive.Partition.History.XmtDelta import XmtDelta
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor


# filtered previous records must end at the wire terminator within the staging capacity
def ReadXmtDeltaMut(CursorValue: XmtCursor) -> XmtDelta:
    Qualifiers: dict[int, bool] = {}
    RestoredValue = ReadUndoRowsMut(CursorValue, Qualifiers, 4096)
    RemovedValue: list[tuple[int, int]] = []
    while IndexValue := CursorValue.ReadIndex():
        KindValue = CursorValue.ReadKind()
        if (
            len(RemovedValue) >= 4096
            or KindValue in (3, 4)
            or KindValue not in KKernelShapes
        ):
            raise ValueError("unqualified rollback removal class or count")
        RemovedValue.append((IndexValue, KindValue))
    CapacityValue = int(UnpackValue(">i", CursorValue.TakeBytes(4))[0])
    if not 0 <= CapacityValue <= 4096:
        raise ValueError("rollback copy capacity is outside its domain")
    PreviousValue = ReadUndoRowsMut(CursorValue, Qualifiers, CapacityValue)
    return XmtDelta(
        RestoredValue,
        tuple(RemovedValue),
        PreviousValue,
        CapacityValue,
        MappingProxyType(Qualifiers),
    )
