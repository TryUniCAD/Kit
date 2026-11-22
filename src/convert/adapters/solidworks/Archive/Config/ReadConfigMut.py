from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.Material.BindMatVisMut import (
    BindMatVisMut,
)
from convert.adapters.solidworks.Archive.Config.ReadCfgBodyMut import ReadCfgBodyMut
from convert.adapters.solidworks.Archive.Config.UseSweepCfgMut import UseSweepCfgMut
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# both body sections consume their complete spans through one map with original header aliases
def ReadConfigMut(
    BufferValue: bytes,
    VersionValue: int,
    HeaderValue: ArchiveNode,
    *,
    UsageValue: BodyUsage | None = None,
    ReadMaterial: bool = False,
) -> ConfigGraph:
    ContextValue = MakeConfigCtx(VersionValue, HeaderValue, UsageValue)
    if ReadMaterial:
        BindMatVisMut(ContextValue)
        UseSweepCfgMut(ContextValue)
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
