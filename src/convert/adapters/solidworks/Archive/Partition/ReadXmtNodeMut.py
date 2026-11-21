from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtArrayMut import (
    ReadXmtArrayMut,
)
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
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
    ShapeValue = KKernelShapes[KindValue]
    if KindValue not in CursorValue.SeenKinds:
        CursorValue.ExpectBytes(SchemaHeader(ShapeValue))
        CursorValue.SeenKinds.add(KindValue)
    ArrayCount = (
        CursorValue.ReadCount()
        if any(FieldValue.CountValue == 1 for FieldValue in ShapeValue.FieldsValue)
        else 0
    )
    if ArrayCount > 4096:
        raise ValueError("current kernel profile array exceeds its bounded owner scope")
    IndexValue = CursorValue.ReadIndex()
    if not IndexValue:
        raise ValueError("current kernel object has a null identity")
    FieldsValue: dict[str, object] = {}
    for FieldValue in ShapeValue.FieldsValue:
        CountValue = ArrayCount if FieldValue.CountValue == 1 else FieldValue.CountValue
        if FieldValue.EncodingValue == "c":
            BytesValue = CursorValue.TakeBytes(
                CountValue if FieldValue.CountValue else 1
            )
            FieldsValue[FieldValue.NameValue] = (
                BytesValue if KindValue == 84 else BytesValue.decode("ascii")
            )
        elif FieldValue.CountValue:
            FieldsValue[FieldValue.NameValue] = ReadXmtArrayMut(
                CursorValue, FieldValue, CountValue, PreviousWorld, ValueReader
            )
        else:
            FieldsValue[FieldValue.NameValue] = ValueReader(
                CursorValue, FieldValue, PreviousWorld
            )
    return XmtNode(IndexValue, KindValue, MappingProxyType(FieldsValue))
