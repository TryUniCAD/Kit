from struct import unpack as UnpackValue

from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# typed scalar decoding keeps native units and pointer domains intact for ownership checks
def ReadXmtValueMut(
    CursorValue: XmtCursor, FieldValue: XmtField, PreviousWorld: bool = False
) -> object:
    Encoding = FieldValue.EncodingValue
    if Encoding == "p":
        IndexValue = CursorValue.ReadIndex()
        if PreviousWorld:
            if IndexValue:
                raise ValueError("only a body free preceding world is qualified")
            CursorValue.ExpectBytes(bytes((1,)))
        return IndexValue
    if Encoding == "v":
        return tuple(
            float(MemberValue)
            for MemberValue in UnpackValue(">ddd", CursorValue.TakeBytes(24))
        )
    Formats = {
        "l": (">B", 1),
        "u": (">B", 1),
        "w": (">H", 2),
        "d": (">i", 4),
        "f": (">d", 8),
    }
    if Encoding not in Formats:
        raise ValueError("kernel scalar encoding is unqualified")
    FormatText, CountValue = Formats[Encoding]
    ScalarValue = UnpackValue(FormatText, CursorValue.TakeBytes(CountValue))[0]
    if Encoding == "f":
        return float(ScalarValue)
    Integer = int(ScalarValue)
    if Encoding == "l" and Integer not in (0, 1):
        raise ValueError("kernel logical scalar is outside its domain")
    return Integer
