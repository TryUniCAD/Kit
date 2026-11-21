from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import (
    EmitAsmStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import (
    MakeAsmHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import (
    MakeAsmBase,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import (
    PutPartRefsMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupIn import (
    CheckGroupIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakeGroupMut import (
    MakeGroupMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# complete planar groups share one generated child while constructing every direct occurrence and ordered explicit endpoint relationship from authored neutral intent
def MakePlanarGroup(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, ...],
    MateInputs: tuple[GroupMateIn, ...],
    FixedIndex: int,
    *,
    DisplayValues: tuple[AsmDisplayIn, ...] | None = None,
) -> OrderedAsm:
    CheckGroupIn(ChildValue, InputValue, Occurrences, MateInputs, FixedIndex)
    StateValue = MakeAsmBase(InputValue)
    HeadersValue = MakeAsmHeaders(StateValue, InputValue)
    References = PutPartRefsMut(
        StateValue, ChildValue, InputValue, Occurrences, HeadersValue
    )
    MateNodes: list[ArchiveNode] = []
    for MateInput in MateInputs:
        MateNodes.append(
            MakeGroupMut(
                StateValue,
                ChildValue,
                InputValue,
                MateInput,
                References,
                HeadersValue,
                tuple(MateNodes),
                FixedIndex,
            )
        )
    MateValues = tuple(MateNodes)
    StreamsValue = EmitAsmStreams(
        StateValue,
        ChildValue,
        InputValue,
        HeadersValue,
        References,
        MateValues,
        DisplayValues=DisplayValues,
    )
    return OrderedAsm(
        StateValue,
        ChildValue,
        References,
        MateValues,
        HeadersValue[0],
        HeadersValue[1],
        StreamsValue.ManagerHeader,
        StreamsValue.DefinitionValue,
        StreamsValue.ConfigValue,
        StreamsValue.ResolvedValue,
        StreamsValue.MatesValue,
        StreamsValue.StreamsValue,
        BuildSldprt(StreamsValue.StreamsValue, FormatVersion=4),
    )
