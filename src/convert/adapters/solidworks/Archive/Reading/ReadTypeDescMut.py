from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ClassIndex import ClassIndex
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# descriptor framing validates the name before the graph can allocate its class
def ReadTypeDescMut(
    Cursor: BinaryReader, *, CanonicalMap: ArchiveMaps | None = None
) -> RuntimeClass:
    Schema = Cursor.ReadUnsigned(2)
    Length = Cursor.ReadUnsigned(2)
    if Length == 0:
        raise ValueError("SOLIDWORKS archive class name must not be empty")
    ClassName = Cursor.TakeBytes(Length).decode("ascii")
    ClassValue = RuntimeClass(ClassName, Schema)
    if CanonicalMap is not None and ClassIndex(CanonicalMap, ClassValue) is not None:
        raise ValueError("SOLIDWORKS archive repeats a canonical class declaration")
    return ClassValue
