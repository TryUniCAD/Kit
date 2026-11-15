from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import ReadSerialized, Serialized

# the sheet record carries this fixed value before the empty string
KSheetMarker = 4

# the sheet record ends with six zero bytes before the count
KSheetTail = 6


# callers need the sheet name scale count and class reference as one value
@dataclass(frozen=True, slots=True)
class SheetRecord:
    NameValue: str
    Scale: float
    Count: int
    ClassRef: int


# the class reference must survive a rewrite so the sheet keeps its type
def SheetRecordAt(DataValue: bytes) -> SheetRecord:
    (ClassRef,) = Struct.unpack_from("<H", DataValue, 0)
    Offset = 2
    NameValue, Offset = ReadSerialized(DataValue, Offset)
    if Offset + 8 + 4 + 4 + 4 + KSheetTail + 2 > len(DataValue):
        raise SldprtFormatError("drawing sheet record is truncated")
    (Scale,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += 8
    (Marker,) = Struct.unpack_from("<I", DataValue, Offset)
    Offset += 4
    (ZeroValue,) = Struct.unpack_from("<I", DataValue, Offset)
    Offset += 4
    EmptyValue, Offset = ReadSerialized(DataValue, Offset)
    if EmptyValue != "" or ZeroValue != 0 or Marker != KSheetMarker:
        raise SldprtFormatError("drawing sheet record is invalid")
    Offset += KSheetTail
    (Count,) = Struct.unpack_from("<H", DataValue, Offset)
    return SheetRecord(NameValue, Scale, Count, ClassRef)


# the writer needs the exact class reference and field order to stay valid
def EncodeSheet(Record: SheetRecord) -> bytes:
    Output = bytearray()
    Output.extend(Struct.pack("<H", Record.ClassRef))
    Output.extend(Serialized(Record.NameValue))
    Output.extend(Struct.pack("<d", Record.Scale))
    Output.extend(Struct.pack("<I", KSheetMarker))
    Output.extend(Struct.pack("<I", 0))
    Output.extend(Serialized(""))
    Output.extend(bytes(KSheetTail))
    Output.extend(Struct.pack("<H", Record.Count))
    return bytes(Output)
