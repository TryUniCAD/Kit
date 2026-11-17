from collections.abc import Callable
from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.CheckConfigLink import CheckConfigLink
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Header.ReadHeadItems import ReadHeadItems
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# one ordinary configuration consumes its complete stream using the original header object identities
def ReadConfigMut(
    BufferValue: bytes,
    VersionValue: int,
    HeaderValue: ArchiveNode,
    *,
    UsageValue: BodyUsage | None = None,
    NodeMaker: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None,
    ReadItems: Callable[[ArchiveNode], tuple[ArchiveNode, ...]] = ReadHeadItems,
) -> ConfigGraph:
    ContextValue = MakeConfigCtx(VersionValue, HeaderValue, UsageValue, ReadItems)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
        NodeFactory=NodeMaker,
    )
    RootValue = RequireConfig(ReadNodeMut(ReaderValue))
    if ReaderValue.Cursor.GetRemaining() != 0:
        raise BodyUnsupported(
            f"SOLIDWORKS configuration has {ReaderValue.Cursor.GetRemaining()} trailing bytes"
        )
    CheckConfigLink(ContextValue)
    ContextValue.UsageValue.IsComplete = True
    return ConfigGraph(
        RootValue,
        HeaderValue,
        ReaderValue.MapValue.Snapshot(),
        ReaderValue.MapValue.BaseValue,
        GetBodyReport(ContextValue.UsageValue),
        VersionValue,
        dict(ContextValue.FlagsValue),
    )
