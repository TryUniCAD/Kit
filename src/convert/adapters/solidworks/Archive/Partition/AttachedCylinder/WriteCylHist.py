from struct import pack as PackValue

from convert.Geometry.Parasolid import EncodePartData, KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.CylJournal import (
    CylJournal,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import (
    MakeEmptyWorld,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteRollMut import (
    WriteRollMut,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import (
    WriteXmtEndMut,
)
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# each physical transmit starts a distinct schema registry and composes its own frame
def EncodeCylFrame(
    NodesValue: tuple[XmtNode, ...],
    RoleValue: bytes,
    JournalValue: CylJournal | None = None,
) -> bytes:
    OutputValue = bytearray(PackValue(">HI", 239, 0))
    SeenKinds: set[int] = set()
    for NodeValue in NodesValue:
        WriteXmtNodeMut(
            OutputValue, NodeValue, KKernelShapes[NodeValue.KindValue], SeenKinds
        )
        if JournalValue is not None and NodeValue is JournalValue.SelectedValue:
            WriteRollMut(
                OutputValue,
                MakeEmptyWorld(1, 1, 0),
                SeenKinds,
                JournalValue.RemovedValues,
            )
        elif JournalValue is not None and NodeValue is JournalValue.ActivationValue:
            WriteRollMut(OutputValue, MakeEmptyWorld(1, 0, 0), SeenKinds)
    WriteXmtEndMut(OutputValue)
    return EncodePartData(
        ParaStream(
            bytes(OutputValue),
            KTerminalFinSchema,
            b": TRANSMIT FILE (" + RoleValue + b") created by modeller version 3701250",
        )
    )


# active topology and a reversible transition share owners yet keep independent transmit framing
def WriteCylHist(
    ActiveValue: tuple[XmtNode, ...],
    JournalValue: CylJournal,
) -> bytes:
    return EncodeCylFrame(ActiveValue, b"partition") + EncodeCylFrame(
        (
            JournalValue.RootValue,
            JournalValue.SelectedValue,
            JournalValue.InitialValue,
            JournalValue.ActivationValue,
        ),
        b"deltas",
        JournalValue,
    )
