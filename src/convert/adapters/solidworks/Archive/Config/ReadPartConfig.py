from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the complete part reader binds its physical configuration and original named model header
def ReadPartConfig(ArchiveValue: SldprtArchive) -> ConfigGraph:
    VersionValue = ContainerMo(ArchiveValue.Streams)
    if ArchiveValue.format_version != 4 or VersionValue != KHeaderVersion:
        raise BodyUnsupported(
            "SOLIDWORKS configuration requires format 4 at version 19000"
        )
    HeaderValue = ReadModelHead(ArchiveValue, VersionValue)
    return ReadConfigMut(
        ArchiveValue.Require("Contents/Config-0"), VersionValue, HeaderValue
    )
