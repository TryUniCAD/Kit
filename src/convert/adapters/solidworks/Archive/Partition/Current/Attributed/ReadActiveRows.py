from collections.abc import Mapping
from types import MappingProxyType

from convert.Geometry.Parasolid import KTerminalFinSchema, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.Current.Attributed.AttributedShapes import (
    KAttributedShapes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtShapeMut import (
    ReadXmtShapeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# active recovery requires every sequential record boundary and the complete terminator
def ReadActiveRows(
    DataValue: bytes,
) -> tuple[Mapping[int, XmtNode], Mapping[int, int]]:
    HeaderValue = ParaHeaderData(DataValue)
    if (
        HeaderValue is None
        or HeaderValue.schema != KTerminalFinSchema
        or HeaderValue.description
        != ": TRANSMIT FILE (partition) created by modeller version 3701250"
    ):
        raise ValueError("unqualified attributed active transmit profile")
    CursorValue = XmtCursor(DataValue[HeaderValue.body_offset :])
    Nodes: dict[int, XmtNode] = {}
    Offsets: dict[int, int] = {}
    while True:
        OffsetValue = CursorValue.OffsetValue
        KindValue = CursorValue.ReadKind()
        if KindValue == 1:
            break
        if KindValue not in KAttributedShapes or len(Nodes) >= 4096:
            raise ValueError("unqualified attributed active record kind or count")
        NodeValue = ReadXmtShapeMut(
            CursorValue, KindValue, KAttributedShapes[KindValue]
        )
        if NodeValue.IndexValue in Nodes:
            raise ValueError("attributed active record identity is ambiguous")
        Nodes[NodeValue.IndexValue] = NodeValue
        Offsets[NodeValue.IndexValue] = OffsetValue
    CursorValue.FinishRead()
    return MappingProxyType(Nodes), MappingProxyType(Offsets)
