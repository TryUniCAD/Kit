from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalRef import ExternalRef
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.WriteClassMut import WriteClassMut
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# object registration precedes recursive fields to preserve shared and cyclic graphs
def WriteObjectMut(
    WriterValue: ObjectStore, NodeValue: ArchiveNode | ExternalRef | None
) -> None:
    if NodeValue is None:
        WriteClassMut(WriterValue, None)
        return
    if isinstance(NodeValue, ExternalRef):
        if NodeValue.IndexValue >= WriterValue.MapValue.BaseValue:
            raise ValueError(
                "external object reference is outside the inherited prefix"
            )
        FindObject(WriterValue.MapValue, NodeValue.IndexValue)
        WriterValue.TagWriter(ArchiveTag("ObjectRef", NodeValue.IndexValue))
        return
    NodeValue = ArchiveNode.RequireNode(NodeValue)
    IndexValue = ObjectIndex(WriterValue.MapValue, NodeValue)
    if IndexValue is not None:
        WriterValue.TagWriter(ArchiveTag("ObjectRef", IndexValue))
        return
    WriteClassMut(WriterValue, NodeValue.ClassValue)
    AddEntryMut(WriterValue.MapValue, NodeValue)
    WriterValue.BodyWriter(NodeValue)
