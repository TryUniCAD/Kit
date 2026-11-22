from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.MakeAsmMgrCtx import MakeAsmMgrCtx
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# serialization recomputes tags counts and map slots from the typed manager graph alone
def WriteCmgrMut(
    RootValue: ArchiveNode,
    VersionValue: int,
    *,
    UsageValue: BodyUsage | None = None,
    AssemblyValue: bool = False,
) -> bytes:
    if RootValue.ClassValue != RuntimeClass("moConfigurationMgr_c", 1):
        raise BodyUnsupported("SOLIDWORKS manager emission requires its concrete root")
    if AssemblyValue:
        Selected = ArchiveNode.RequireNode(RootValue.FieldsValue["f368"])
        if Selected.ClassValue != RuntimeClass("moConfiguration_c", 1):
            raise BodyUnsupported(
                "SOLIDWORKS assembly manager needs its selected configuration"
            )
    MakeContext = MakeAsmMgrCtx if AssemblyValue else MakeCmgrContext
    ContextValue = MakeContext(VersionValue, UsageValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, RootValue)
    ContextValue.UsageValue.IsComplete = True
    return bytes(WriterValue.OutputValue)
