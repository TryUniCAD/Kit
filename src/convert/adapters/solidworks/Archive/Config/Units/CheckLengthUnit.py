from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the ordinary override is an optional distinct length owner in the current table
def CheckLengthUnit(UnitValue: ArchiveNode, MapValue: ArchiveMaps) -> None:
    OverrideValue = UnitValue.FieldsValue["fb8"]
    if OverrideValue is None:
        return
    NodeValue = ArchiveNode.RequireNode(OverrideValue)
    IndexValue = ObjectIndex(MapValue, NodeValue)
    if (
        IndexValue is None
        or IndexValue < MapValue.BaseValue
        or NodeValue.ClassValue != UnitValue.ClassValue
        or NodeValue.FieldsValue["fb8"] is not None
    ):
        raise BodyUnsupported("SOLIDWORKS unit table has the wrong length override")
