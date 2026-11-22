from dataclasses import replace as ReplaceValue
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import (
    MakeAsmHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import (
    MakeAsmBase,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmGraphs import (
    MakeAsmGraphs,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetMut import (
    CheckTargetMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.ReadTargetBox import (
    ReadTargetBox,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetAudit import (
    TargetAudit,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.CheckNestedMut import (
    CheckNestedMut,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.EmitNestedAsm import (
    EmitNestedAsm,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakePlacedRefs import (
    MakePlacedRefs,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.PublishRefsMut import (
    PublishRefsMut,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt


# a true recursive assembly must derive every reference count bound header stream and container from actual generated targets and authored rigid placements
def MakeNestedMut(
    InputValue: AssemblyInput,
    Placements: tuple[TargetPlacement, ...],
    AuditValue: TargetAudit | None = None,
) -> TargetDocument:
    ScopeValue = TargetAudit() if AuditValue is None else AuditValue
    CheckNestedMut(InputValue, Placements, ScopeValue)
    StateValue = MakeAsmBase(InputValue)
    HeadersValue = MakeAsmHeaders(StateValue, InputValue)
    References = MakePlacedRefs(
        StateValue, HeadersValue[0], Placements, InputValue.TargetValue
    )
    PublishRefsMut(StateValue, HeadersValue, Placements, References)
    GraphValue = MakeAsmGraphs(StateValue, InputValue, HeadersValue[0])
    TargetValue = TargetDocument(
        StateValue.RootValue,
        StateValue.ManagerValue,
        StateValue.CurrentConfig,
        HeadersValue[0],
        HeadersValue[1],
        GraphValue.ManagerHeader,
        StateValue.FeatureValues,
        ReadTargetBox(StateValue.RootValue),
        References,
        tuple(ItemValue.TargetValue for ItemValue in Placements),
        sum(1 + ItemValue.TargetValue.ActivityValue for ItemValue in Placements),
        GraphValue.ConfigValue,
        GraphValue.ResolvedValue,
        {},
        b"",
    )
    StreamsValue = EmitNestedAsm(
        StateValue, InputValue, HeadersValue, GraphValue, TargetValue
    )
    ResultValue = ReplaceValue(
        TargetValue,
        StreamsValue=StreamsValue.StreamsValue,
        BytesValue=BuildSldprt(StreamsValue.StreamsValue, FormatVersion=4),
    )
    CheckTargetMut(ResultValue, ScopeValue)
    return ResultValue
