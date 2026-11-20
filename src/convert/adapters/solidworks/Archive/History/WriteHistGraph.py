from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.History.CheckHistRoot import CheckHistRoot
from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.History.MakeHistCtx import MakeHistCtx
from convert.adapters.solidworks.Archive.History.ReadHistGraph import ReadHistGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# reading back the emitted buffer ties observed node offsets to the returned bytes
def WriteHistGraph(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, HistoryGraph]:
    RootValue = CheckHistRoot(RootValue)
    ContextValue = MakeHistCtx(VersionValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    BufferValue = bytes(WriterValue.OutputValue)
    return BufferValue, ReadHistGraph(BufferValue, VersionValue)
