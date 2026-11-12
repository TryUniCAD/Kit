from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from tests.convert.formats.FusionCodec.Entities.WireJson import WireJson


def ReadWire(Value: WireJson) -> WireType:
    return WireType(
        Value["KindValue"],
        tuple(ReadWire(Entry) for Entry in Value["Arguments"]),
        tuple(
            FieldSpec(
                Entry["FieldName"], ReadWire(Entry["ValueType"]), Entry["IsSaved"]
            )
            for Entry in Value["Members"]
        ),
        Value["ClassGuid"],
        Value["FixedCount"],
        tuple(Value["AllowedInts"]),
        Value["HasMatrixRows"],
    )
