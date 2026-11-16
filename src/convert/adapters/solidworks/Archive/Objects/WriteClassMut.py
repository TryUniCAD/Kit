from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.BindClassMut import BindClassMut
from convert.adapters.solidworks.Archive.Maps.ClassIndex import ClassIndex
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# inherited class identities must remain references rather than fabricated new descriptors
def WriteClassMut(
    WriterValue: ObjectStore, ClassValue: RuntimeClass | ExternalClass | None
) -> None:
    if ClassValue is None:
        WriterValue.TagWriter(ArchiveTag("Null", None))
        return
    if isinstance(ClassValue, ExternalClass):
        BindClassMut(WriterValue.MapValue, ClassValue)
        WriterValue.TagWriter(ArchiveTag("ClassRef", ClassValue.IndexValue))
        return
    IndexValue = ClassIndex(WriterValue.MapValue, ClassValue)
    if IndexValue is not None:
        WriterValue.TagWriter(ArchiveTag("ClassRef", IndexValue))
        return
    WriterValue.TagWriter(ArchiveTag("NewClass", None))
    WriterValue.ClassWriter(ClassValue)
    _ = AddEntryMut(WriterValue.MapValue, ClassValue)
