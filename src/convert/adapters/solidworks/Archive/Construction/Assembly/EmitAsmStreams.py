from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyStreams import (
    AssemblyStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.MakeAsmVisual import (
    MakeAsmVisual,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)


# flat and ordered callers must preserve exact bytes while recursive assemblies share the same linked binary graph and manager publication
def EmitAsmStreams(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    References: tuple[ArchiveNode, ...],
    MateValue: ArchiveNode | tuple[ArchiveNode, ...],
    *,
    DisplayValues: tuple[AsmDisplayIn, ...] | None = None,
) -> AssemblyStreams:
    MateRoots = (MateValue,) if isinstance(MateValue, ArchiveNode) else MateValue
    VisualBytes = (
        None
        if DisplayValues is None
        else MakeAsmVisual(
            StateValue, ChildValue, HeadersValue, References, MateRoots, DisplayValues
        )
    )
    GraphValue = MakeAsmGraphs(StateValue, InputValue, HeadersValue[0], MateRoots)
    StreamsValue = MakeAsmAux(
        StateValue,
        ChildValue,
        InputValue,
        HeadersValue,
        GraphValue.ManagerHeader,
        GraphValue.DefinitionValue,
        References,
        DisplayName=(
            DisplayValues[0].NameValue
            if DisplayValues is not None and type(ChildValue.PlanValue) is BlindPlan
            else None
        ),
    )
    Combined = JoinAsmMut(StateValue, GraphValue, StreamsValue)
    if VisualBytes is not None:
        Combined.StreamsValue[KVisualStream] = VisualBytes
    return Combined
