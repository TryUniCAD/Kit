from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakeTargetRef import (
    MakeTargetRef,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakeTargetDirs import (
    MakeTargetDirs,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# recursive occurrences must share their real target directory and the containing file while allocating native feature ids in authored order
def MakePlacedRefs(
    StateValue: AssemblyState,
    HeaderValue: ArchiveNode,
    Placements: tuple[TargetPlacement, ...],
    FeatureValue: FeatureTarget,
) -> tuple[ArchiveNode, ...]:
    Directories = MakeTargetDirs(Placements)
    OwnerFile = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f38"])
    return tuple(
        MakeTargetRef(
            StateValue,
            ItemValue.TargetValue,
            Directories[id(ItemValue.TargetValue.RootValue)],
            OwnerFile,
            ItemValue.OccurrenceValue,
            FeatureValue,
            OrdinalValue,
        )
        for OrdinalValue, ItemValue in enumerate(
            Placements, len(StateValue.FeatureValues) - 1
        )
    )
