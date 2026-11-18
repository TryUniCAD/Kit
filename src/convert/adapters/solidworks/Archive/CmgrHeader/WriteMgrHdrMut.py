from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerContext import ManagerContext
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerGraph import ManagerGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a lightweight configuration directory must derive every count tag and byte from its actual projected manager records
def WriteMgrHdrMut(
    RootValue: ArchiveNode, VersionValue: int
) -> tuple[bytes, ManagerGraph]:
    if RootValue.ClassValue != RuntimeClass("dmConfigMgrHeader_c", 1):
        raise BodyUnsupported(
            "configuration manager header requires its concrete native root"
        )
    ContextValue = ManagerContext(VersionValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue), ManagerGraph(
        RootValue,
        WriterValue.MapValue.Snapshot(),
        VersionValue,
        GetBodyReport(ContextValue.UsageValue),
    )
