from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.CmgrHeader.CheckMgrRows import CheckMgrRows
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerContext import ManagerContext
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerGraph import ManagerGraph
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import KManagerClass
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a lightweight configuration directory must derive every count tag and byte from its actual projected manager records
def WriteMgrHeader(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, ManagerGraph]:
    if RootValue.ClassValue != KManagerClass:
        raise BodyUnsupported(
            "configuration manager header requires its concrete native root"
        )
    ContextValue = ManagerContext(VersionValue)
    CheckMgrRows(RootValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue), ManagerGraph(
        RootValue,
        WriterValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
