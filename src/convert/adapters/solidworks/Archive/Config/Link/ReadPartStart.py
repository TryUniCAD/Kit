from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Link.CfgPartStart import CfgPartStart
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import CheckPartRoot
from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


# physical root allocation precedes the zero byte handoff within the lightweight section
def ReadPartStart(ArchiveValue: SldprtArchive) -> CfgPartStart:
    VersionValue = ContainerMo(ArchiveValue.Streams)
    if ArchiveValue.format_version != 4 or VersionValue != KHeaderVersion:
        raise BodyUnsupported(
            "SOLIDWORKS configuration start requires format 4 at version 19000"
        )
    HeaderValue = ReadModelHead(ArchiveValue, VersionValue)
    NodesValue = HeaderRefNodes(HeaderValue, VersionValue)
    Cursor = BinaryReader(ArchiveValue.Require("Contents/Config-0"))
    MapValue = ArchiveMaps(1)
    RootValue = ReadNodeMut(GraphReader(Cursor, MapValue, CheckPartRoot))
    if RootValue is None:
        raise BodyUnsupported("SOLIDWORKS configuration start requires a current part")
    LightSize = Cursor.ReadUnsigned(4)
    if not 8 <= LightSize <= Cursor.GetRemaining():
        raise BodyUnsupported(
            "SOLIDWORKS configuration lightweight section is unbounded"
        )
    RootValue.EndOffset = None
    BindNodesMut(MapValue, NodesValue)
    return CfgPartStart(
        HeaderValue,
        RootValue,
        MapValue.Snapshot(),
        MapValue.BaseValue,
        Cursor.GetOffset(),
        LightSize,
    )
