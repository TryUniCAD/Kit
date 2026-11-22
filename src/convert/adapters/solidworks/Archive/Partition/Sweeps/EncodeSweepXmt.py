from struct import pack as PackValue

from convert.Geometry.Parasolid import KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import (
    WriteXmtEndMut,
)
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.GetXmtField import (
    GetXmtField,
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

# ghost partitions have a distinct native header description from their embedded standalone sheet
KSweepGhostDescription = (
    b": TRANSMIT FILE (partition) created by modeller version 3701250"
)


# these local analytic cells must use canonical resident indices and complete internal references
def CheckSweepNodes(NodesValue: tuple[XmtNode, ...], IsPartition: bool) -> None:
    KindValue = 101 if IsPartition else 12
    if not 0 < len(NodesValue) <= KLocalLimit or NodesValue[0].KindValue != KindValue:
        raise ValueError("sweep transmit requires its actual world or standalone sheet")
    for IndexValue, NodeValue in enumerate(NodesValue, 1):
        if (
            NodeValue.IndexValue != IndexValue
            or NodeValue.KindValue not in KLocalShapes
            and NodeValue.KindValue != KindValue
        ):
            raise ValueError("sweep transmit requires ordered known resident cells")
        ShapeValue = KKernelShapes[NodeValue.KindValue]
        for FieldValue in ShapeValue.FieldsValue:
            if FieldValue.EncodingValue == "p" and any(
                type(PointerValue) is not int
                or not 0 <= PointerValue <= len(NodesValue)
                for PointerValue in GetXmtField(NodeValue, FieldValue)[1]
            ):
                raise ValueError("sweep kernel cell has a detached resident link")


# sweep sheets and attributed partitions reuse the typed native node codec and stream framing
def EncodeSweepXmt(NodesValue: tuple[XmtNode, ...], IsPartition: bool) -> bytes:
    CheckSweepNodes(NodesValue, IsPartition)
    OutputValue = bytearray(PackValue(">HI", 239, 0))
    SeenKinds: set[int] = set()
    for NodeValue in NodesValue:
        WriteXmtNodeMut(
            OutputValue, NodeValue, KKernelShapes[NodeValue.KindValue], SeenKinds
        )
    WriteXmtEndMut(OutputValue)
    Description = KSweepGhostDescription if IsPartition else KLocalDescription
    return ParaStream(bytes(OutputValue), KTerminalFinSchema, Description)
