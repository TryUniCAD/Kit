from struct import pack as PackValue

from convert.Geometry.Parasolid import KTerminalFinSchema, ParaStream, WritePointerMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.CheckLocalXmt import (
    CheckLocalXmt,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalDescription,
    KLocalLimit,
    KLocalShapes,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylGraph import (
    CheckCylGraph,
)


# generated imports need a native local transmit from model owned node fields alone
def EncodeLocalXmt(
    NodeValues: tuple[XmtNode, ...], SchemaValue: str = KTerminalFinSchema
) -> bytes:
    if type(SchemaValue) is not str or SchemaValue != KTerminalFinSchema:
        raise ValueError("local kernel transmit schema is unqualified")
    if type(NodeValues) is not tuple or not 0 < len(NodeValues) <= KLocalLimit:
        raise ValueError("local kernel node count is outside the resident domain")
    OutputValue = bytearray(PackValue(">HI", 239, 0))
    SeenKinds: set[int] = set()
    NodesValue: dict[int, XmtNode] = {}
    for IndexValue, NodeValue in enumerate(NodeValues, 1):
        if (
            type(NodeValue) is not XmtNode
            or type(NodeValue.IndexValue) is not int
            or NodeValue.IndexValue != IndexValue
            or type(NodeValue.KindValue) is not int
            or NodeValue.KindValue not in KLocalShapes
        ):
            raise ValueError(
                "local kernel nodes require canonical indices and qualified classes"
            )
        RecordValue = XmtNode(
            IndexValue, NodeValue.KindValue, dict(NodeValue.FieldsValue)
        )
        WriteXmtNodeMut(
            OutputValue, RecordValue, KLocalShapes[RecordValue.KindValue], SeenKinds
        )
        NodesValue[IndexValue] = RecordValue
    if any(NodeValue.KindValue in (31, 51) for NodeValue in NodesValue.values()):
        CheckCylGraph(NodesValue)
    else:
        CheckLocalXmt(NodesValue)
    OutputValue.extend(PackValue(">H", 1))
    WritePointerMut(OutputValue, 0)
    return ParaStream(bytes(OutputValue), SchemaValue, KLocalDescription)
