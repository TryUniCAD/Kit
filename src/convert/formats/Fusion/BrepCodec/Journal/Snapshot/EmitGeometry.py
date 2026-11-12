from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


def EmitGeometry(Model: GeometryState) -> bytes:
    CheckGeometry(Model)
    Payload = (
        EmitBrepHeader(Model.Stamp, Model.Header.RootCount, False, 10.0)
        + b"".join(EmitWireRecord(MakeEntityNode(Value)) for Value in Model.Entities)
        + EncodeSmbName("End-of-ASM-data")
    )
    if len(Payload) > 2 * 1024 * 1024:
        raise ValueError("Encoded Fusion geometry exceeds its byte quota")
    return Payload
