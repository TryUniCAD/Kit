from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag


# structural tags must use the shared native reference grammar in every body stream
def WriteTagMut(WriterValue: BodyWriter, TagValue: ArchiveTag) -> None:
    WriterValue.OutputValue.extend(EncodeTag(TagValue))


# runtime class descriptors carry declared vocabulary rather than saved object field values
def WriteTypeMut(WriterValue: BodyWriter, ClassValue: RuntimeClass) -> None:
    NameBytes = ClassValue.NameValue.encode("ascii")
    WriterValue.OutputValue.extend(EncodeScalar(ClassValue.SchemaValue, "u16"))
    WriterValue.OutputValue.extend(EncodeScalar(len(NameBytes), "u16"))
    WriterValue.OutputValue.extend(NameBytes)
