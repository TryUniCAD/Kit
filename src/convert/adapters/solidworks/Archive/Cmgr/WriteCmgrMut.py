from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# serialization recomputes tags counts and map slots from the typed manager graph alone
def WriteCmgrMut(
    RootValue: ArchiveNode, VersionValue: int, *, UsageValue: BodyUsage | None = None
) -> bytes:
    ContextValue = MakeCmgrContext(VersionValue, UsageValue)
    if RootValue.ClassValue != RuntimeClass("moConfigurationMgr_c", 1):
        raise BodyUnsupported("SOLIDWORKS manager emission requires its concrete root")
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue)
