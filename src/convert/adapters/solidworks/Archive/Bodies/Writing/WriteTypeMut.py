from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# runtime class descriptors carry declared vocabulary rather than saved object field values
def WriteTypeMut(WriterValue: BodyWriter, ClassValue: RuntimeClass) -> None:
    NameBytes = ClassValue.NameValue.encode("ascii")
    WriterValue.OutputValue.extend(EncodeScalar(ClassValue.SchemaValue, "u16"))
    WriterValue.OutputValue.extend(EncodeScalar(len(NameBytes), "u16"))
    WriterValue.OutputValue.extend(NameBytes)
