from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a shared map alias cannot qualify as a newly owned scene child or name
def RequireNewNode(Value: object, MapValue: ArchiveMaps) -> ArchiveNode:
    if not isinstance(Value, ArchiveNode):
        raise BodyUnsupported("SOLIDWORKS scene requires a concrete owned node")
    IndexValue = ObjectIndex(MapValue, Value)
    if IndexValue is None or IndexValue < MapValue.BaseValue:
        raise BodyUnsupported("SOLIDWORKS scene cannot borrow an earlier object")
    return Value
