from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Container.Format import KLocalBodyStream


# body labels must follow the same local group that owns the decoded geometry
def ReadLocalWrap(StreamData: bytes, LocalData: bytes) -> str:
    Cursor = BinaryReader(StreamData)
    if Cursor.ReadUnsigned(4) != 1:
        raise ValueError("local body partition requires one storage group")
    KeyValue = ReadCStringMut(Cursor)
    if (
        not KeyValue.IsUnicode
        or not KeyValue.TextValue
        or not KeyValue.TextValue.isprintable()
    ):
        raise ValueError("local body group has an unqualified storage key")
    Counts = tuple(Cursor.ReadUnsigned(4) for _ in range(3))
    if Counts != (0, 1, 0) or Cursor.ReadUnsigned(1) != 0:
        raise ValueError("local body group has unqualified ownership or presence")
    RecordLength = Cursor.ReadUnsigned(4)
    if (
        RecordLength <= 1
        or RecordLength != Cursor.GetRemaining()
        or Cursor.ReadUnsigned(1) != 0
    ):
        raise ValueError("local body group has an unqualified record boundary")
    BodyData = Cursor.TakeBytes(RecordLength - 1)
    Values = DecodePartData(BodyData, KLocalBodyStream)
    if len(Values) != 1 or (
        Values[0].wrapper_offset != 0
        or Values[0].stored_size != len(BodyData)
        or Values[0].data != LocalData
    ):
        raise ValueError("local body group does not own the selected geometry")
    return KeyValue.TextValue
