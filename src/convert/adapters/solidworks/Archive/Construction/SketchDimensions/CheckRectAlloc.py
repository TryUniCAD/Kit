from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)


# both retained dimension identities must fit before publication can partially consume the model allocator
def CheckRectAlloc(Allocator: PersistentIds) -> None:
    if not isinstance(CastValue(object, Allocator), PersistentIds):
        raise TypeError("rectangle dimensions require the shared model allocator")
    NextValue = Allocator.NextValue
    for _ in range(2):
        while NextValue in Allocator.ReservedSet:
            NextValue += 1
        if NextValue >= 0x7FFFFFFF:
            raise ValueError(
                "persistent id space cannot allocate both rectangle drivers"
            )
        NextValue += 1
