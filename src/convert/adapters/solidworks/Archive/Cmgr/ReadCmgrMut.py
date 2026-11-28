from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from collections.abc import Callable
from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# ordinary managers own a fresh map and must consume their complete typed stream
def ReadCmgrMut(
    BufferValue: bytes,
    VersionValue: int,
    *,
    UsageValue: BodyUsage | None = None,
    ReadLinked: bool = False,
    NodeMaker: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None,
) -> CmgrGraph:
    ContextValue = MakeCmgrContext(VersionValue, UsageValue, ReadLinked=ReadLinked)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
        NodeFactory=NodeMaker,
    )
    RootValue = ReadNodeMut(ReaderValue)
    if RootValue is None or RootValue.ClassValue != RuntimeClass(
        "moConfigurationMgr_c", 1
    ):
        raise BodyUnsupported(
            "SOLIDWORKS manager stream requires its configuration manager root"
        )
    if ReaderValue.Cursor.GetRemaining() != 0:
        raise BodyUnsupported(
            f"SOLIDWORKS manager has {ReaderValue.Cursor.GetRemaining()} trailing bytes"
        )
    ContextValue.UsageValue.IsComplete = True
    return CmgrGraph(
        RootValue,
        ReaderValue.MapValue.Snapshot(),
        GetBodyReport(ContextValue.UsageValue),
        VersionValue,
        dict(ContextValue.FlagsValue),
    )
