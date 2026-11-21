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
    ResultValue: dict[int, ArchiveNode] = {}
    for ItemValue in Placements:
        IdentityValue = id(ItemValue.TargetValue.RootValue)
        if IdentityValue not in ResultValue:
            UsersValue = sum(
                OtherValue.TargetValue.RootValue is ItemValue.TargetValue.RootValue
                for OtherValue in Placements
            )
            ResultValue[IdentityValue] = MakeTargetDir(
                ItemValue.TargetValue, UsersValue, len(ResultValue)
            )
    return ResultValue
