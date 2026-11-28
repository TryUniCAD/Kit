from typing import Never

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
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
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# an exact part owned interval retains its typed body and relative extent
def ReadCfgMaster(
    BufferValue: bytes,
    VersionValue: int,
    PartValue: ArchiveNode,
    MapValue: ArchiveMaps,
) -> ArchiveNode:
    ContextValue = MakeMasterCtx(VersionValue, PartValue, MapValue)
    Cursor = BinaryReader(BufferValue)
    ReaderValue = GraphReader(
        Cursor, MapValue, DenyMasterNode, RequireCanonicalTags=True
    )
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope({}),
        PartValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadFieldsMut(FrameValue, KMasterRule)
    if Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS sheet metal master has trailing data")
    NodeValue = ArchiveNode.RequireNode(FrameValue.ScopeValue.FieldsValue[KMasterField])
    CheckMasterBody(NodeValue)
    return NodeValue


# the empty master profile cannot open any tagged child body
def DenyMasterNode(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> Never:
    ClassName = NodeValue.ClassValue.NameValue
    Offset = ReaderValue.Cursor.GetOffset()
    raise BodyUnsupported(
        f"SOLIDWORKS sheet metal master has an unsupported mapped child {ClassName} at {Offset}"
    )
