from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.MakePropContext import (
    MakePropContext,
)


# a present empty file scope owns a container even when its property lists are absent
def WriteEmptyProps(VersionValue: int) -> bytes:
    ContextValue = MakePropContext(VersionValue)
    FileOwner = ArchiveNode(
        RuntimeClass("moFilePropContainer_c", 1), {"f08": None, "f10": None}
    )
    Container = ArchiveNode(
        RuntimeClass("moCusPropContainer_c", 1),
        {"f08": FileOwner, "f10": None, "f18": None, "f20": 0},
    )
    RootValue = ArchiveNode(
        RuntimeClass("moCusPropMgr_c", 1),
        {"f0c": -1, "f08": 1, "f20": ({"key": 0, "o": Container},), "f54": 0},
    )
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    return bytes(WriterValue.OutputValue)
