from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import ReadSerialized, Serialized

# the style record ends with a one byte terminator and a two byte class reference
KStyleTerminator = 1
KStyleClassRef = 2


# callers need the style name description pattern and class reference as one value
@dataclass(frozen=True, slots=True)
class LineStyle:
    Name: str
    Description: str
    Values: tuple[float, ...]
    ClassRef: int | None


# the terminator decides whether a class reference follows the pattern
def LineStyles(DataValue: bytes) -> tuple[LineStyle, ...]:
    Result: list[LineStyle] = []
    Offset = 0
    while Offset < len(DataValue):
        NameValue, Offset = ReadSerialized(DataValue, Offset)
        Description, Offset = ReadSerialized(DataValue, Offset)
        if Offset + 2 > len(DataValue):
            raise SldprtFormatError("drawing line style is truncated")
        (Count,) = Struct.unpack_from("<H", DataValue, Offset)
        Offset += 2
        if Offset + Count * 8 > len(DataValue):
            raise SldprtFormatError("drawing line style is truncated")
        Values = Struct.unpack_from("<" + "d" * Count, DataValue, Offset)
        Offset += Count * 8
        if Offset >= len(DataValue):
            raise SldprtFormatError("drawing line style is truncated")
        Terminator = DataValue[Offset]
        Offset += 1
        ClassRef: int | None = None
        if Terminator == 0:
            if Offset + KStyleClassRef > len(DataValue):
                raise SldprtFormatError("drawing line style is truncated")
            (ClassRef,) = Struct.unpack_from("<H", DataValue, Offset)
            Offset += KStyleClassRef
        elif Terminator != KStyleTerminator:
            raise SldprtFormatError("drawing line style terminator is invalid")
        Result.append(LineStyle(NameValue, Description, Values, ClassRef))
    return tuple(Result)


# the writer needs the exact terminator and class reference to keep the block valid
def EncodeStyles(Styles: tuple[LineStyle, ...]) -> bytes:
    Output = bytearray()
    for Index, Style in enumerate(Styles):
        Output.extend(Serialized(Style.Name))
        Output.extend(Serialized(Style.Description))
        Output.extend(Struct.pack("<H", len(Style.Values)))
        for Value in Style.Values:
            Output.extend(Struct.pack("<d", Value))
        if Index + 1 < len(Styles):
            if Style.ClassRef is None:
                raise SldprtFormatError("drawing line style class reference is missing")
            Output.extend(Struct.pack("<BH", 0, Style.ClassRef))
        else:
            Output.extend(Struct.pack("<B", KStyleTerminator))
    return bytes(Output)
