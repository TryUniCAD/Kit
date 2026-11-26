from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# inherited resolved maps must retain one actual configuration model instead of anonymous prefix placeholders
def FindModelRoot(SeedValue: MapSnapshot) -> ArchiveNode:
    RootsValue = tuple(
        Entry.EntryValue
        for Entry in SeedValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue
        in (RuntimeClass("moPart_c", 1), RuntimeClass("moAssembly_c", 1))
    )
    if len(RootsValue) != 1:
        raise BodyUnsupported(
            "ordinary resolved graph requires one concrete inherited configuration model"
        )
    return RootsValue[0]
