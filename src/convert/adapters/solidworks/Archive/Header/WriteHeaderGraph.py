from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.WriteHeaderBody import StoreHeaderBody
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag


# standalone headers each derive a fresh native object map from their root
def WriteHeadGraph(RootValue: ArchiveNode, Version: int) -> bytes:
    if Version != KHeaderVersion:
        raise ValueError(f"unsupported SOLIDWORKS header archive version {Version}")
    if RootValue.ClassValue != RuntimeClass("moHeader_c", 1):
        raise ValueError("SOLIDWORKS header requires a current native header root")
    Buffer = bytearray()

    # tag lengths and indexes derive from the archive map
    def StoreTag(TagValue: ArchiveTag) -> None:
        Buffer.extend(EncodeTag(TagValue))

    # class records derive name length from the selected runtime class
    def StoreClass(ClassValue: RuntimeClass) -> None:
        NameValue = ClassValue.NameValue.encode("ascii")
        Buffer.extend(PackValue("<HH", ClassValue.SchemaValue, len(NameValue)))
        Buffer.extend(NameValue)

    # retained child references enter the same stream allocation as their owner
    def StoreBody(NodeValue: ArchiveNode) -> None:
        StoreHeaderBody(Buffer, WriterValue, NodeValue)

    WriterValue = ObjectStore(ArchiveMaps(1), StoreTag, StoreClass, StoreBody)
    WriteObjectMut(WriterValue, RootValue)
    return bytes(Buffer)
