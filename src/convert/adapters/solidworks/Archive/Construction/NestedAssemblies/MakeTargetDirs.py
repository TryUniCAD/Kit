from collections import Counter as CountItems

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakeTargetDir import (
    MakeTargetDir,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# each direct generated definition needs one native directory record counted by actual placements and numbered in first use order
def MakeTargetDirs(
    Placements: tuple[TargetPlacement, ...],
) -> dict[int, ArchiveNode]:
    UseCounts = CountItems(
        id(ItemValue.TargetValue.RootValue) for ItemValue in Placements
    )
    ResultValue: dict[int, ArchiveNode] = {}
    for ItemValue in Placements:
        IdentityValue = id(ItemValue.TargetValue.RootValue)
        if IdentityValue not in ResultValue:
            ResultValue[IdentityValue] = MakeTargetDir(
                ItemValue.TargetValue, UseCounts[IdentityValue], len(ResultValue)
            )
    return ResultValue
