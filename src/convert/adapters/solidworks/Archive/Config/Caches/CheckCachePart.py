from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the ordinary cache fields are owned by a concrete part root
KCachePart = RuntimeClass("moPart_c", 1)


# the caller must supply its actual mapped part and concrete descriptor
def CheckCachePart(PartValue: ArchiveNode, MapValue: ArchiveMaps) -> None:
    if (
        PartValue.ClassValue != KCachePart
        or KCachePart not in MapValue.ClassLookup
        or ObjectIndex(MapValue, PartValue) is None
    ):
        raise BodyUnsupported(
            "SOLIDWORKS cache requires its mapped ordinary part owner"
        )
