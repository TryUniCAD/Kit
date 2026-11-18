from convert.adapters.solidworks.Archive.Construction.Assembly.AsmCandidate import (
    AsmCandidate,
)
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
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt


# a complete ordinary assembly must synthesize every native stream from its actual generated child and authored placements without any file or cad runtime reads
def MakeAssembly(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    MateValue: AssemblyMateIn,
) -> AsmCandidate:
    CheckAsmInput(ChildValue, InputValue, Occurrences, MateValue)
    StateValue = MakeAsmBase(InputValue)
    HeadersValue = MakeAsmHeaders(StateValue, InputValue)
    References = PutOccsMut(
        StateValue, ChildValue, InputValue, Occurrences, HeadersValue
    )
    MateNode = MakeAsmMateMut(
        StateValue, ChildValue, InputValue, MateValue, References, HeadersValue
    )
    StreamsValue = EmitAsmStreams(
        StateValue, ChildValue, InputValue, HeadersValue, References, MateNode
    )
    BytesValue = BuildSldprt(StreamsValue.StreamsValue, FormatVersion=4)
    return AsmCandidate(
        StateValue,
        ChildValue,
        References,
        MateNode,
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
