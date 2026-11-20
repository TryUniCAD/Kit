from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# descriptor framing validates the name before the graph can allocate its class
def ReadTypeDescMut(Cursor: BinaryReader) -> RuntimeClass:
    Schema = Cursor.ReadUnsigned(2)
    Length = Cursor.ReadUnsigned(2)
    if Length == 0:
        raise ValueError("SOLIDWORKS archive class name must not be empty")
    ClassName = Cursor.TakeBytes(Length).decode("ascii")
    return RuntimeClass(ClassName, Schema)
