from struct import pack as PackValue

from convert.Geometry.Parasolid import WritePointerMut
from convert.adapters.solidworks.Archive.Partition.Fields.WorldShapes import (
    KWorldShapes,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import (
    WriteXmtEndMut,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a retained rollback can reverse attached residents before restoring the preceding world
def WriteRollMut(
    OutputValue: bytearray,
    WorldValue: XmtNode,
    SeenKinds: set[int],
    RemovedValues: tuple[XmtNode, ...] = (),
) -> None:
    WriteXmtEndMut(OutputValue)
    for NodeValue in RemovedValues:
        WritePointerMut(OutputValue, NodeValue.IndexValue)
        OutputValue.extend(PackValue(">H", NodeValue.KindValue))
    WritePointerMut(OutputValue, 0)
    OutputValue.extend(PackValue(">i", 1))
    WriteXmtNodeMut(
        OutputValue, WorldValue, KWorldShapes[101], SeenKinds, PreviousWorld=True
    )
    WriteXmtEndMut(OutputValue)
