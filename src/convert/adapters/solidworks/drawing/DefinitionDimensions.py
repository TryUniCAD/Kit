from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import ReadSerialized, Serialized

# the parameter record is a fixed width
KParameterWidth = 76

# the parameter record carries a two byte gap after the text
KParameterGap = 2

# the parameter record carries three zero bytes after the measured value
KParameterZero = 3

# the parameter record carries one flag byte after the zero run
KParameterFlag = 1

# the parameter record carries twenty reserved bytes before the count
KParameterReserved = 20

# the parameter record carries eight trailing bytes after the count
KParameterTail = 8


# callers need the dimension name and its decoded fields as one value
@dataclass(frozen=True, slots=True)
class DimensionParam:
    ClassRef: int
    NameValue: str
    Value: float
    FlagValue: int
    UnitValue: int
    TextValue: str
    GapBytes: bytes
    Measured: float
    ZeroRun: bytes
    FlagByte: int
    Reserved: bytes
    Count: int
    TailBytes: bytes


# the parameter record is read as one fixed width value
def ParameterAt(DataValue: bytes, Offset: int) -> tuple[DimensionParam, int]:
    Start = Offset
    (ClassRef,) = Struct.unpack_from("<H", DataValue, Offset)
    Offset += 2
    NameValue, Offset = ReadSerialized(DataValue, Offset)
    (Value,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += 8
    (FlagValue,) = Struct.unpack_from("<i", DataValue, Offset)
    Offset += 4
    (UnitValue,) = Struct.unpack_from("<i", DataValue, Offset)
    Offset += 4
    TextValue, Offset = ReadSerialized(DataValue, Offset)
    GapBytes = DataValue[Offset : Offset + KParameterGap]
    Offset += KParameterGap
    (Measured,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += 8
    ZeroRun = DataValue[Offset : Offset + KParameterZero]
    Offset += KParameterZero
    FlagByte = DataValue[Offset]
    Offset += KParameterFlag
    Reserved = DataValue[Offset : Offset + KParameterReserved]
    Offset += KParameterReserved
    (Count,) = Struct.unpack_from("<i", DataValue, Offset)
    Offset += 4
    TailBytes = DataValue[Offset : Offset + KParameterTail]
    Offset += KParameterTail
    if Offset - Start != KParameterWidth:
        raise SldprtFormatError("drawing dimension parameter width is invalid")
    return (
        DimensionParam(
            ClassRef,
            NameValue,
            Value,
            FlagValue,
            UnitValue,
            TextValue,
            GapBytes,
            Measured,
            ZeroRun,
            FlagByte,
            Reserved,
            Count,
            TailBytes,
        ),
        Offset,
    )


# the writer needs the exact field order and gaps to stay valid
def EncodeParameter(Parameter: DimensionParam) -> bytes:
    Output = bytearray()
    Output.extend(Struct.pack("<H", Parameter.ClassRef))
    Output.extend(Serialized(Parameter.NameValue))
    Output.extend(Struct.pack("<d", Parameter.Value))
    Output.extend(Struct.pack("<i", Parameter.FlagValue))
    Output.extend(Struct.pack("<i", Parameter.UnitValue))
    Output.extend(Serialized(Parameter.TextValue))
    Output.extend(Parameter.GapBytes)
    Output.extend(Struct.pack("<d", Parameter.Measured))
    Output.extend(Parameter.ZeroRun)
    Output.extend(bytes((Parameter.FlagByte,)))
    Output.extend(Parameter.Reserved)
    Output.extend(Struct.pack("<i", Parameter.Count))
    Output.extend(Parameter.TailBytes)
    return bytes(Output)
