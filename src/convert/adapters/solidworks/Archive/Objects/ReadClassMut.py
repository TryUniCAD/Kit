from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ReadTypeMut import ReadTypeMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# class only sites reject object references instead of guessing a descriptor
def ReadClassMut(ReaderValue: ObjectRead) -> RuntimeClass | ExternalClass | None:
    TagValue = ReaderValue.TagReader()
    if TagValue.KindValue == "Null":
        return None
    return ReadTypeMut(ReaderValue, TagValue)
