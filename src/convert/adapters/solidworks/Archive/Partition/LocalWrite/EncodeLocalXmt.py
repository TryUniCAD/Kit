from struct import pack as PackValue

from convert.Geometry.Parasolid import KTerminalFinSchema, ParaStream, WritePointerMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.BindLocalAttrs import (
    BindLocalAttrs,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.CheckXmtLink import (
    CheckXmtLink,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalBodyOwner import (
    LocalBodyOwner,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalDescription,
    KLocalLimit,
    KOwnedShapes,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.RequireLocalXmt import (
    RequireLocalXmt,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# generated imports serialize only a validated bare graph and its computed optional owners
def EncodeLocalXmt(
    NodeValues: tuple[XmtNode, ...],
    SchemaValue: str = KTerminalFinSchema,
    *,
    OwnerValue: LocalBodyOwner | None = None,
) -> bytes:
    if type(SchemaValue) is not str or SchemaValue != KTerminalFinSchema:
        raise ValueError("local kernel transmit schema is unqualified")
    RowsValue = RequireLocalXmt(NodeValues)
    if OwnerValue is not None:
        if type(OwnerValue) is not LocalBodyOwner:
            raise TypeError("local kernel attributes need typed owner identities")
        RowsValue = BindLocalAttrs(RowsValue, OwnerValue)
    if len(RowsValue) > KLocalLimit:
        raise ValueError(
            "attributed local kernel node count exceeds the resident domain"
        )
    OutputValue = bytearray(PackValue(">HI", 239, 0))
    SeenKinds: set[int] = set()
    if OwnerValue is not None:
        NodesValue = {NodeValue.IndexValue: NodeValue for NodeValue in RowsValue}
        for NodeValue in RowsValue:
            CheckXmtLink(NodesValue, NodeValue, KOwnedShapes[NodeValue.KindValue])
    for NodeValue in RowsValue:
        WriteXmtNodeMut(
            OutputValue, NodeValue, KOwnedShapes[NodeValue.KindValue], SeenKinds
        )
    OutputValue.extend(PackValue(">H", 1))
    WritePointerMut(OutputValue, 0)
    return ParaStream(bytes(OutputValue), SchemaValue, KLocalDescription)
