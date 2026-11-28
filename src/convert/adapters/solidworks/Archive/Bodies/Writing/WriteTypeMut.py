from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Objects.ClassDescField import (
    KClassDescWord,
    KClassNameCodec,
)


# runtime class descriptors carry declared vocabulary rather than saved object field values
def WriteTypeMut(WriterValue: BodyWriter, ClassValue: RuntimeClass) -> None:
    NameBytes = ClassValue.NameValue.encode(KClassNameCodec)
    WriterValue.OutputValue.extend(KClassDescWord.pack(ClassValue.SchemaValue))
    WriterValue.OutputValue.extend(KClassDescWord.pack(len(NameBytes)))
    WriterValue.OutputValue.extend(NameBytes)
