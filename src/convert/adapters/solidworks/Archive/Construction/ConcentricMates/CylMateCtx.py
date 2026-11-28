from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# component wrappers must draw their distinct timestamps from the actual parent and child owners
@DataClass(frozen=True, slots=True)
class CylMateCtx:
    StateValue: AssemblyState
    InputValue: AssemblyInput
    ChildValue: PartCandidate
    HeadersValue: tuple[ArchiveNode, ArchiveNode]
