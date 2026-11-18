from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import (
    MakePartTarget,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakeTargetDir import (
    MakeTargetDir,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a repeated generated child has one directory record with independent child file and manager save events and users derived from actual occurrences
def MakeDirectory(ChildValue: PartCandidate, UsersValue: int) -> ArchiveNode:
    return MakeTargetDir(MakePartTarget(ChildValue), UsersValue)
