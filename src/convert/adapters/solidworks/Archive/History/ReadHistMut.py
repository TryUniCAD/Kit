from functools import partial as PartialValue
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.History.CheckHistRoot import CheckHistRoot
from convert.adapters.solidworks.Archive.History.HistoryContext import HistoryContext
from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# independent metadata readback must consume the entire ordinary stream and preserve actual typed graph identities without opaque tails
def ReadHistMut(BufferValue: bytes, VersionValue: int) -> HistoryGraph:
    ContextValue = HistoryContext(VersionValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
    )
    RootValue = CheckHistRoot(ReadNodeMut(ReaderValue))
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported("ordinary history stream has trailing data")
    ContextValue.UsageValue.IsComplete = True
    return HistoryGraph(
        RootValue,
        ReaderValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
