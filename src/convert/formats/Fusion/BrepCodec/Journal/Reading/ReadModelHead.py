from struct import unpack as UnpackValue

from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckModelHead import (
    CheckModelHead,
)
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmToken


def ReadModelHead(
    Cursor: MetaCursor, HasHistory: bool
) -> tuple[BrepHeader, GeometryStamp]:
    if Cursor.TakeBytes(15) != b"ASM BinaryFile8":
        raise ValueError("Unsupported Fusion geometry signature")
    Version, Stored, Roots, Flags = UnpackValue("<4q", Cursor.TakeBytes(32))
    if Stored != 0:
        raise ValueError("Unsupported Fusion stored entity-count header")
    Strings: list[str] = []
    Numbers: list[float] = []
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor)
        if TagValue != 7 or not isinstance(Value, str):
            raise ValueError("Invalid Fusion geometry provenance")
        Strings.append(Value)
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor)
        if TagValue != 6 or not isinstance(Value, float):
            raise ValueError("Invalid Fusion geometry header scalar")
        Numbers.append(Value)
    Header = BrepHeader(Version, Roots, Flags, *Numbers)
    CheckModelHead(Header, HasHistory)
    return Header, GeometryStamp(*Strings)
