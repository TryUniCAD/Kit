from struct import Struct

from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Native import ReadSerialized

# the local group header bounds the compressed body owned by the native feature
KLocalBoxHdr = Struct("<IIIBI")


# the exact storage key must identify the group that holds the selected payload
def ReadLocalWrap(StreamData: bytes, LocalData: bytes) -> str:
    if StreamData[:4] != bytes((1, 0, 0, 0)):
        raise ValueError("local body requires one storage group")
    KeyValue, KeyEnd = ReadSerialized(StreamData, 4)
    BodyStart = KeyEnd + KLocalBoxHdr.size
    if not KeyValue.isprintable() or BodyStart >= len(StreamData):
        raise ValueError("local body group has an unqualified key or boundary")
    BeforeCount, BodyCount, AfterCount, FlagValue, BodySize = KLocalBoxHdr.unpack_from(
        StreamData, KeyEnd
    )
    if (
        (BeforeCount, BodyCount, AfterCount, FlagValue) != (0, 1, 0, 0)
        or BodySize <= 1
        or BodySize != len(StreamData) - BodyStart
        or StreamData[BodyStart]
    ):
        raise ValueError("local body group has an unqualified record boundary")
    BodyData = StreamData[BodyStart + 1 :]
    Values = DecodePartData(BodyData, KLocalBodyStream)
    if len(Values) != 1 or (
        Values[0].wrapper_offset != 0
        or Values[0].stored_size != len(BodyData)
        or Values[0].data != LocalData
    ):
        raise ValueError("local body group does not own the selected geometry")
    return KeyValue
