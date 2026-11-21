from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.History.ReadHistGraph import ReadHistGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# reading back the emitted buffer ties observed node offsets to the returned bytes
def WriteHistGraph(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, HistoryGraph]:
    BufferValue, _ = WriteHistMut(RootValue, VersionValue)
    return BufferValue, ReadHistGraph(BufferValue, VersionValue)
