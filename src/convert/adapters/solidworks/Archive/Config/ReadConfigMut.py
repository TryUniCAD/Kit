from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import CheckPartRoot
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# the native root must be admitted before any configuration section fields execute
def ReadCfgBodyMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    if NodeValue.StartOffset == 0:
        CheckPartRoot(ReaderValue, NodeValue)
        ContextValue.PartRootValue = NodeValue
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)


# both body sections consume their complete spans through one map with original header aliases
def ReadConfigMut(
    BufferValue: bytes,
    VersionValue: int,
    HeaderValue: ArchiveNode,
    *,
    UsageValue: BodyUsage | None = None,
) -> ConfigGraph:
    ContextValue = MakeConfigCtx(VersionValue, HeaderValue, UsageValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadCfgBodyMut, ContextValue),
    )
    RootValue = RequireConfig(ReadNodeMut(ReaderValue))
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported(
            f"SOLIDWORKS configuration has {ReaderValue.Cursor.GetRemaining()} trailing bytes"
        )
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
