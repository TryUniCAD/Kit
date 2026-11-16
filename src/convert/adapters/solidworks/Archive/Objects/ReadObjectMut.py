from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalRef import ExternalRef
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ReadTypeMut import ReadTypeMut


# nodes enter the shared map before their bodies so cycles resolve by identity
def ReadObjectMut(ReaderValue: ObjectRead) -> ArchiveNode | ExternalRef | None:
    StartOffset = ReaderValue.ReadOffset()
    TagValue = ReaderValue.TagReader()
    if TagValue.KindValue == "Null":
        return None
    if TagValue.KindValue == "ObjectRef":
        if TagValue.IndexValue is None:
            raise ValueError("archive object reference has no index")
        return FindObject(ReaderValue.MapValue, TagValue.IndexValue)
    ClassValue = ReadTypeMut(ReaderValue, TagValue)
    NodeValue = ArchiveNode.RequireNode(ReaderValue.NodeFactory(ClassValue))
    if NodeValue.ClassValue != ClassValue:
        raise ValueError("archive node factory changed the declared class")
    if ObjectIndex(ReaderValue.MapValue, NodeValue) is not None:
        raise ValueError("archive node factory reused an existing mapped object")
    NodeValue.StartOffset = StartOffset
    NodeValue.EndOffset = None
    NodeValue.IndexValue = AddEntryMut(ReaderValue.MapValue, NodeValue)
    ReaderValue.BodyReader(NodeValue)
    NodeValue.EndOffset = ReaderValue.ReadOffset()
    return NodeValue
