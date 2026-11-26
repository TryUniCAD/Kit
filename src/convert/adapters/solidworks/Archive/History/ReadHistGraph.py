from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.History.CheckHistRoot import CheckHistRoot
from convert.adapters.solidworks.Archive.History.HistoryGraph import HistoryGraph
from convert.adapters.solidworks.Archive.History.MakeHistCtx import MakeHistCtx
from convert.adapters.solidworks.Archive.History.ReadHistBodyMut import ReadHistBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# the standalone metadata reader must consume the whole stream and keep its own object map
def ReadHistGraph(BufferValue: bytes, VersionValue: int) -> HistoryGraph:
    ContextValue = MakeHistCtx(VersionValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadHistBodyMut, ContextValue),
    )
    RootValue = CheckHistRoot(ReadNodeMut(ReaderValue))
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS history stream has trailing data")
    ContextValue.UsageValue.IsComplete = True
    return HistoryGraph(
        RootValue,
        ReaderValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
