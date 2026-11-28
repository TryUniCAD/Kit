from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyMateIn import (
    AssemblyMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmInput import (
    CheckAsmInput,
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
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmMateMut import (
    MakeAsmMateMut,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutOccsMut import (
    PutOccsMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# an ordered assembly must construct every authored mate through the same actual graph factories allocator and header publication without resetting prior state
def MakeOrderedAsm(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    MateInputs: tuple[AssemblyMateIn, ...],
) -> OrderedAsm:
    if (
        type(MateInputs) is not tuple
        or not MateInputs
        or any(type(Value) is not AssemblyMateIn for Value in MateInputs)
    ):
        raise ValueError(
            "ordered assembly requires a nonempty explicit typed mate sequence"
        )
    if (
        len({Value.NameValue for Value in MateInputs}) != len(MateInputs)
        or len({Value.FixedIndex for Value in MateInputs}) != 1
    ):
        raise ValueError(
            "ordered assembly requires distinct mate names and the same actual fixed anchor"
        )
    for MateInput in MateInputs:
        CheckAsmInput(ChildValue, InputValue, Occurrences, MateInput)
    StateValue = MakeAsmBase(InputValue)
    HeadersValue = MakeAsmHeaders(StateValue, InputValue)
    References = PutOccsMut(
        StateValue, ChildValue, InputValue, Occurrences, HeadersValue
    )
    MateNodes: list[ArchiveNode] = []
    for MateInput in MateInputs:
        MateNodes.append(
            MakeAsmMateMut(
                StateValue,
                ChildValue,
                InputValue,
                MateInput,
                References,
                HeadersValue,
                tuple(MateNodes),
            )
        )
    MateValues = tuple(MateNodes)
    StreamsValue = EmitAsmStreams(
        StateValue, ChildValue, InputValue, HeadersValue, References, MateValues
    )
    BytesValue = BuildSldprt(StreamsValue.StreamsValue, FormatVersion=4)
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
        BytesValue,
    )
