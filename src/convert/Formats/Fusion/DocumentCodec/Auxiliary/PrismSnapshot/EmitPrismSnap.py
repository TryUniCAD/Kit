from convert.Formats.Fusion.BrepCodec.Prism.Writing.EmitPrismRows import EmitPrismRows
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckSnapshot import (
    CheckSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.SnapRecords import (
    SnapRecords,
)
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from dataclasses import replace as ReplaceValue
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry


# the prism snapshot operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitPrismSnap(Value: PrismSnapshot) -> bytes:
    CheckSnapshot(Value)
    Records = SnapRecords(Value)
    CheckBrepRefs(Records, 4)
    Payload = (
        EmitBrepHeader(Value.Stamp, 4, False, 10.0)
        + EmitPrismRows(Records)
        + EncodeSmbName("End-of-ASM-data")
    )
    if Value.Header.IntWidth == 4:
        Payload = EmitGeometry(ReplaceValue(ReadGeometry(Payload), Header=Value.Header))
    return Payload
