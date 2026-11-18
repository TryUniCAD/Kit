from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import (
    MakePartTarget,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakeTargetRef import (
    MakeTargetRef,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# existing ordinary part callers must retain the same generated reference graph while subassembly placement shares its native construction rules
def MakeOccurrence(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    Directory: ArchiveNode,
    OwnerFile: ArchiveNode,
    InputValue: OccurrenceIn,
    TargetValue: FeatureTarget,
    BoundsValue: dict[str, float],
    OrdinalValue: int,
) -> ArchiveNode:
    ChildTarget = MakePartTarget(ChildValue)
    if dict(ChildTarget.BoundsValue) != BoundsValue:
        raise ValueError("part reference bounds must match the actual generated child")
    return MakeTargetRef(
        StateValue,
        ChildTarget,
        Directory,
        OwnerFile,
        InputValue,
        TargetValue,
        OrdinalValue,
    )
