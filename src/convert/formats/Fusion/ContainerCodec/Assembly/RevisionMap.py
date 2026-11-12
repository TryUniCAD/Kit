from uuid import UUID as ParseUuid

from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair

KChangeTypes = (
    "Appearance",
    "Geometry",
    "PhysicalMaterial",
    "Properties",
    "StructureChange",
    "Transform",
)


def RevisionMap(Value: str) -> ValueMap:
    Identifier = ParseUuid(Value)
    if not Identifier.int or str(Identifier) != Value:
        raise ValueError("Invalid Fusion assembly revision identifier")
    return ValueMap(tuple(ValuePair(NameValue, Value) for NameValue in KChangeTypes))
