from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmNum,
    ReadAsmText,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadIdentity(Table: AsmTable, Mapping: dict[int, int]) -> BodyIdentity:
    BodyRoot = RequireAsm(Table, Mapping[1], "body", 6)
    Timestamp = RequireAsm(Table, Mapping[26], "ATTRIB_CUSTOM-attrib", 8)
    Generic = RequireAsm(Table, Mapping[27], "ATTRIB_CUSTOM-attrib", 16)
    Operation = ReadAsmText(Generic, 12)
    Number = int(Operation)
    if str(Number) != Operation:
        raise ValueError("Invalid Fusion BRep body operation identity")
    return BodyIdentity(
        ReadAsmInt(BodyRoot, 1),
        Number,
        ReadAsmInt(Generic, 13),
        ReadAsmNum(Timestamp, 7),
    )
