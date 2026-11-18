from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import (
    PutPartRefsMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the established pair interface must retain its exact two component result while sharing native direct occurrence publication with complete planar groups
def PutOccsMut(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
) -> tuple[ArchiveNode, ArchiveNode]:
    if len(Occurrences) != 2:
        raise ValueError("the pair composer requires exactly two authored occurrences")
    References = PutPartRefsMut(
        StateValue, ChildValue, InputValue, Occurrences, HeadersValue
    )
    return References[0], References[1]
