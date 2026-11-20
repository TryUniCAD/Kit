from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.History.CheckHistRoot import CheckHistRoot
from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.History.MakeHistCtx import MakeHistCtx
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the metadata writer must regenerate all tags and counts from the actual typed model
def WriteHistGraph(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, HistoryGraph]:
    RootValue = CheckHistRoot(RootValue)
    ContextValue = MakeHistCtx(VersionValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue), HistoryGraph(
        RootValue,
        WriterValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
