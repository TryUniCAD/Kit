from struct import unpack as UnpackValue

from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import (
    KAsmWidths,
    KIntCodes,
    ReadAsmToken,
)


# the boundary representation head operation needs a distinct decoding boundary so topology identity survives native history reconstruction
def ReadBrepHeadMut(
    Cursor: MetaCursor, HasHistory: bool
) -> tuple[BrepHeader, GeometryStamp]:
    Width = KAsmWidths.get(Cursor.TakeBytes(15))
    if Width is None:
        raise ValueError("Unsupported Fusion BRep binary header")
    Version, Stored, Roots, Flags = UnpackValue(
        "<4" + KIntCodes[Width][1], Cursor.TakeBytes(4 * Width)
    )
    if (Version, Stored, Roots, Flags) != (
        23200,
        0,
        2 if HasHistory else 4,
        3 if HasHistory else 2,
    ):
        raise ValueError("Unsupported Fusion BRep header profile")
    Strings: list[str] = []
    Numbers: list[float] = []
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor, Width)
        if TagValue != 7 or not isinstance(Value, str):
            raise ValueError("Invalid Fusion BRep provenance field")
        Strings.append(Value)
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor, Width)
        if TagValue != 6 or not isinstance(Value, float):
            raise ValueError("Invalid Fusion BRep numeric header")
        Numbers.append(Value)
    if tuple(Numbers) != (50.0 if HasHistory else 10.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion BRep scale or tolerances")
    Header = BrepHeader(
        Version, Roots, Flags, Numbers[0], Numbers[1], Numbers[2], Width
    )
    return Header, GeometryStamp(*Strings)
