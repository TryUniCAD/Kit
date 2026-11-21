from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.History.CheckHistRoot import CheckHistRoot
from convert.adapters.solidworks.Archive.History.HistoryContext import HistoryContext
from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# metadata emission must derive object tags counts strings and every scalar from the actual newly constructed graph
def WriteHistMut(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, HistoryGraph]:
    RootValue = CheckHistRoot(RootValue)
    ContextValue = HistoryContext(VersionValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue), HistoryGraph(
        RootValue,
        WriterValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
