from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyStreams import (
    AssemblyStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.JoinAsmMut import (
    JoinAsmMut,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmGraphs import (
    MakeAsmGraphs,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.MakeAsmAux import (
    MakeAsmAux,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# flat and ordered callers must preserve exact bytes while recursive assemblies share the same linked binary graph and manager publication
def EmitAsmStreams(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    References: tuple[ArchiveNode, ...],
    MateValues: tuple[ArchiveNode, ...],
) -> AssemblyStreams:
    GraphValue = MakeAsmGraphs(StateValue, InputValue, HeadersValue[0], MateValues)
    StreamsValue = MakeAsmAux(
        StateValue,
        ChildValue,
        InputValue,
        HeadersValue,
        GraphValue.ManagerHeader,
        GraphValue.DefinitionValue,
        References,
    )
    return JoinAsmMut(StateValue, GraphValue, StreamsValue)
