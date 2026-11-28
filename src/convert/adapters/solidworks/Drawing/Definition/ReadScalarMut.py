from struct import Struct as ScalarLayout
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader

# wire scalar kinds keep signed flags and floating coordinates distinct
KScalarTypes = MappingProxyType(
    {
        "i8": ScalarLayout("<b"),
        "u8": ScalarLayout("<B"),
        "i16": ScalarLayout("<h"),
        "u16": ScalarLayout("<H"),
        "i32": ScalarLayout("<i"),
        "u32": ScalarLayout("<I"),
        "i64": ScalarLayout("<q"),
        "u64": ScalarLayout("<Q"),
        "f32": ScalarLayout("<f"),
        "f64": ScalarLayout("<d"),
    }
)


# scalar reads advance the same bounded cursor as native graph and text values
def ReadScalarMut(Cursor: BinaryReader, KindName: str) -> int | float:
    Layout = KScalarTypes[KindName]
    Number = Layout.unpack(Cursor.TakeBytes(Layout.size))[0]
    if not isinstance(Number, (int, float)):
        raise ValueError("invalid SOLIDWORKS scalar kind")
    return Number


# size and flag operands must have an exact integer wire type before use
def TakeWireInt(Number: object) -> int:
    if type(Number) is not int:
        raise ValueError("SOLIDWORKS drawing archive expected an integer")
    return Number
