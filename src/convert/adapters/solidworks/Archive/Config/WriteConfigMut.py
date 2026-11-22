from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Config.WriteCfgBodyMut import WriteCfgBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# configuration emission derives every section length and alias slot from the same typed part model
def WriteConfigMut(
    RootValue: ArchiveNode,
    VersionValue: int,
    HeaderValue: ArchiveNode,
    *,
    UsageValue: BodyUsage | None = None,
    SweepGhosts: bool = False,
) -> tuple[bytes, ConfigGraph]:
    RootValue = RequireConfig(RootValue)
    ContextValue = MakeConfigCtx(
        VersionValue, HeaderValue, UsageValue, SweepGhosts=SweepGhosts
    )
    ContextValue.PartRootValue = RootValue
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteCfgBodyMut)
    WriteNodeMut(WriterValue, RootValue)
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
