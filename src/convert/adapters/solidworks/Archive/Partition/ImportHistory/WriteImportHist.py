from struct import pack as PackValue

from convert.Geometry.Parasolid import EncodePartData, KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Partition.Fields.WorldShapes import (
    KWorldShapes,
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
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the configuration stream needs separate frame and schema state for its active and rollback transmits
def WriteImportHist(
    WorldValue: XmtNode, RootValue: XmtNode, MarkValues: tuple[XmtNode, ...]
) -> bytes:
    PrefixValue = PackValue(">HI", 239, 0)
    ActiveValue = bytearray(PrefixValue)
    WriteXmtNodeMut(ActiveValue, WorldValue, KWorldShapes[101], set())
    WriteXmtEndMut(ActiveValue)
    HistoryValue = bytearray(PrefixValue)
    SeenKinds: set[int] = set()
    WriteXmtNodeMut(HistoryValue, RootValue, KWorldShapes[3], SeenKinds)
    SelectedIndex = RootValue.Integer("current_pmark")
    for MarkValue in MarkValues:
        WriteXmtNodeMut(HistoryValue, MarkValue, KWorldShapes[4], SeenKinds)
        if MarkValue.Integer("delta_key"):
            PriorValue = MakeEmptyWorld(
                WorldValue.IndexValue, int(MarkValue.IndexValue == SelectedIndex), 0
            )
            WriteRollMut(HistoryValue, PriorValue, SeenKinds)
    WriteXmtEndMut(HistoryValue)
    return b"".join(
        EncodePartData(
            ParaStream(
                bytes(BufferValue),
                KTerminalFinSchema,
                b": TRANSMIT FILE ("
                + RoleValue
                + b") created by modeller version 3701250",
            )
        )
        for BufferValue, RoleValue in (
            (ActiveValue, b"partition"),
            (HistoryValue, b"deltas"),
        )
    )
