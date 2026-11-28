from collections.abc import Callable

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckConfigLink import CheckConfigLink
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Config.WriteCfgBodyMut import WriteCfgBodyMut
from convert.adapters.solidworks.Archive.Header.ReadHeadItems import ReadHeadItems
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# configuration emission derives every section tag count and map slot from the typed graph
def WriteConfigMut(
    RootValue: ArchiveNode,
    VersionValue: int,
    HeaderValue: ArchiveNode,
    *,
    UsageValue: BodyUsage | None = None,
    ReadItems: Callable[[ArchiveNode], tuple[ArchiveNode, ...]] = ReadHeadItems,
    PartRelations: bool = False,
) -> tuple[bytes, ConfigGraph]:
    RootValue = RequireConfig(RootValue, PartRelations=PartRelations)
    ContextValue = MakeConfigCtx(
        VersionValue, HeaderValue, UsageValue, ReadItems, PartRelations=PartRelations
    )
    if RootValue.ClassValue == KPartRoot:
        ContextValue.PartRootValue = RootValue
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteCfgBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    CheckConfigLink(ContextValue)
    ContextValue.UsageValue.IsComplete = True
    GraphValue = ConfigGraph(
        RootValue,
        HeaderValue,
        WriterValue.MapValue.Snapshot(),
        WriterValue.MapValue.BaseValue,
        GetBodyReport(ContextValue.UsageValue),
        VersionValue,
        dict(ContextValue.FlagsValue),
    )
    return bytes(WriterValue.OutputValue), GraphValue
