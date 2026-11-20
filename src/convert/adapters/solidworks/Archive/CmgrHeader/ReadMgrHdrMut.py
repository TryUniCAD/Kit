from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.CmgrHeader.CheckMgrRows import CheckMgrRows
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerContext import ManagerContext
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerGraph import ManagerGraph
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import KManagerClass
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrNodeMut import ReadMgrNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# current manager header readback must preserve complete typed rows and refuse unknown roots or trailing opaque data
def ReadMgrHdrMut(BufferValue: bytes, VersionValue: int) -> ManagerGraph:
    ContextValue = ManagerContext(VersionValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadMgrNodeMut, ContextValue),
    )
    RootValue = ReadNodeMut(ReaderValue)
    if (
        RootValue is None
        or RootValue.ClassValue != KManagerClass
        or ReaderValue.Cursor.GetRemaining()
    ):
        raise BodyUnsupported(
            "configuration manager header has an unsupported root or trailing data"
        )
    CheckMgrRows(RootValue)
    ContextValue.UsageValue.IsComplete = True
    return ManagerGraph(
        RootValue,
        ReaderValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
