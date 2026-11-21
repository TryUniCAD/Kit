from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Master.CheckMasterBody import (
    CheckMasterBody,
)
from convert.adapters.solidworks.Archive.Config.Master.MakeMasterCtx import (
    MakeMasterCtx,
)
from convert.adapters.solidworks.Archive.Config.Master.MasterLayout import (
    KMasterField,
    KMasterRule,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# master emission derives the owned body without changing its parent or linked map
def WriteCfgMaster(
    NodeValue: ArchiveNode,
    VersionValue: int,
    PartValue: ArchiveNode,
    MapValue: ArchiveMaps,
) -> bytes:
    ContextValue = MakeMasterCtx(VersionValue, PartValue, MapValue)
    CheckMasterBody(NodeValue)
    WriterValue = BodyWriter(MapValue, ContextValue, WriteBodyMut)
    ScopeValue = FieldScope({KMasterField: NodeValue})
    FrameValue = WriteFrame(
        WriterValue, ScopeValue, PartValue, WriteSchemaMut, WriteFieldsMut
    )
    WriteFieldsMut(FrameValue, KMasterRule)
    return bytes(WriterValue.OutputValue)
