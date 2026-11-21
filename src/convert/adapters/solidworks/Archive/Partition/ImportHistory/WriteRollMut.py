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


# a retained import rollback keeps one preceding world without local body deletion records
def WriteRollMut(
    OutputValue: bytearray, WorldValue: XmtNode, SeenKinds: set[int]
) -> None:
    WriteXmtEndMut(OutputValue)
    WritePointerMut(OutputValue, 0)
    OutputValue.extend(PackValue(">i", 1))
    WriteXmtNodeMut(
        OutputValue, WorldValue, KWorldShapes[101], SeenKinds, PreviousWorld=True
    )
    WriteXmtEndMut(OutputValue)
