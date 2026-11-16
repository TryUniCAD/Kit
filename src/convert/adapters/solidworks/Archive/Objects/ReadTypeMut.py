from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.FindClass import FindClass
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# class declarations allocate exactly once before an object body can begin
def ReadTypeMut(
    ReaderValue: ObjectRead, TagValue: ArchiveTag
) -> RuntimeClass | ExternalClass:
    if TagValue.KindValue == "NewClass":
        ClassValue = ReaderValue.ClassReader()
        if type(ClassValue) is not RuntimeClass:
            raise TypeError("new archive class requires a complete runtime descriptor")
        _ = AddEntryMut(ReaderValue.MapValue, ClassValue)
        return ClassValue
    if TagValue.KindValue == "ClassRef" and TagValue.IndexValue is not None:
        return FindClass(ReaderValue.MapValue, TagValue.IndexValue)
    raise ValueError("expected a new class or class reference tag")
