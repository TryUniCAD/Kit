from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KHeaderFields,
    KHeaderVersion,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# both optional representations must survive a full header graph write and read
def TestHeadBounds() -> None:
    Fields: dict[str, object] = {
        FieldName: 0 if WireKind in {"B", "H", "I", "i"} else None
        for FieldName, WireKind in KHeaderFields
    }
    for Bounds in (None, (1.0, 2.0, 3.0, -4.0, -5.0, -6.0, 7.0, 8.0, 9.0, 10.0)):
        Fields["bbox"] = Bounds
        Fields["fcc"] = -1
        RootNode = ArchiveNode(RuntimeClass("moHeader_c", 1), Fields)
        WireBytes = WriteHeadGraph(RootNode, KHeaderVersion)
        Decoded = ReadHeaderGraph(WireBytes, KHeaderVersion)
        assert Decoded.FieldsValue["bbox"] == Bounds
        assert Decoded.FieldsValue["fcc"] == -1
