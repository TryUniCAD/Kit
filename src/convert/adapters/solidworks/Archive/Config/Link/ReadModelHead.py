from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive


# configuration aliases come from the separately stored model header role
def ReadModelHead(ArchiveValue: SldprtArchive, VersionValue: int) -> ArchiveNode:
    return ReadHeaderGraph(
        ArchiveValue.Require("Contents/Config-0-ModelHeader"), VersionValue
    )
