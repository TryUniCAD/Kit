from collections.abc import Mapping
from types import MappingProxyType

from convert.Geometry.Parasolid import KTerminalFinSchema, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# named solids must come from the complete active payload of the pinned kernel format
def ReadActiveNodes(
    DataValue: bytes,
    *,
    Description: str = ": TRANSMIT FILE (partition) created by modeller version 3701250",
) -> Mapping[int, XmtNode]:
    HeaderValue = ParaHeaderData(DataValue)
    if (
        HeaderValue is None
        or HeaderValue.schema != KTerminalFinSchema
        or HeaderValue.description != Description
    ):
        raise ValueError("active kernel transmit profile is unqualified")
    CursorValue = XmtCursor(DataValue[HeaderValue.body_offset :])
    NodesValue: dict[int, XmtNode] = {}
    while (KindValue := CursorValue.ReadKind()) != 1:
        NodeValue = ReadXmtNodeMut(CursorValue, KindValue)
        if (
            NodeValue.IndexValue in NodesValue
            or KindValue in (3, 4)
            or len(NodesValue) >= 4096
        ):
            raise ValueError("active kernel graph has ambiguous ownership")
        NodesValue[NodeValue.IndexValue] = NodeValue
    CursorValue.FinishRead()
    return MappingProxyType(NodesValue)
