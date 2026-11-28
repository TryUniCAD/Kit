from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)


# both dimension and mate ids must fit before either actual native node consumes shared persistent allocation state
def RequireIdRoom(Allocator: PersistentIds) -> None:
    NextValue = Allocator.NextValue
    for _ in range(2):
        while NextValue in Allocator.ReservedSet:
            NextValue += 1
        if NextValue >= 0x7FFFFFFF:
            raise ValueError(
                "distance dimension and mate exceed persistent id capacity"
            )
        NextValue += 1
