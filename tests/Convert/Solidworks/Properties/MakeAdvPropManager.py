from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.ManagerFields import (
    KManagerFields,
    KManagerSchemas,
)


# complete container tests need newly encoded keyed owners without copying any native property stream
def MakeAdvPropManager(PolicyValue: int) -> bytes:
    FileValue = ArchiveNode(
        RuntimeClass("moFilePropContainer_c", 1), {"f08": None, "f10": None}
    )
    CutValue = ArchiveNode(
        RuntimeClass("moCutListPropContainer_c", 1), {"f08": (), "f38": ()}
    )
    Container = ArchiveNode(
        RuntimeClass("moCusPropContainer_c", 1),
        {"f08": FileValue, "f10": CutValue, "f18": None, "f20": 0},
    )
    Root = ArchiveNode(
        RuntimeClass("moCusPropMgr_c", 1),
        {"f0c": -1, "f08": PolicyValue, "f20": ({"key": 0, "o": Container},), "f54": 0},
    )
    Context = BodyContext(
        19000, KManagerFields, {}, KManagerSchemas, NewBodyUsage(19000, None)
    )
    Writer = BodyWriter(ArchiveMaps(1), Context, WriteBodyMut)
    WriteNodeMut(Writer, Root)
    return bytes(Writer.OutputValue)
