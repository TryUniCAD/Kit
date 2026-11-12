from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireField import EmitWireField
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def EmitWireRecord(Record: AsmRecord) -> bytes:
    if len(Record.Tokens) > 4096:
        raise ValueError("Oversized Fusion journal wire record")
    return (
        EncodeSmbName(Record.Name)
        + b"".join(EmitWireField(Field) for Field in Record.Tokens)
        + b"\x11"
    )
