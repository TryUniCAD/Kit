from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitResolvedStream
from convert.adapters.solidworks.Core.TypedResolved.Materials.BindNamedMat import (
    BindNamedMat,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatTree import (
    CheckMatTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.NamedMatRead import (
    NamedMatRead,
)


# assigned material inspection is deliberately explicit and reads only its bounded ordinary part profile
def ReadNamedMat(ArchiveValue: SldprtArchive) -> NamedMatRead:
    StreamsValue = ArchiveValue.Streams
    ConfigName = "Contents/Config-0"
    VersionValue = ContainerMo(StreamsValue)
    if (
        ArchiveValue.format_version != 4
        or VersionValue != KHeaderVersion
        or KitResolvedStream in StreamsValue
        or any(
            StreamName.startswith("Contents/Config-")
            and StreamName != ConfigName
            and not StreamName.startswith(ConfigName + "-")
            for StreamName in StreamsValue
        )
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material requires an ordinary version-19000 part Config-0"
        )
    PartGraph = ReadConfigMut(
        ArchiveValue.Require(ConfigName),
        VersionValue,
        ReadModelHead(ArchiveValue, VersionValue),
        ReadMaterial=True,
    )
    ManagerValue = ReadCmgrMut(
        ArchiveValue.Require("Contents/CMgr"), VersionValue, ReadMaterial=True
    )
    HeaderValue = ReadMgrHeader(ArchiveValue.Require("Contents/CMgrHdr2"), VersionValue)
    ReadValue = BindNamedMat(PartGraph, ManagerValue, HeaderValue)
    CheckMatTree(ArchiveValue.Require("swXmlContents/MATERIALTREE"), ReadValue)
    return ReadValue
