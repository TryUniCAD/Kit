from convert.adapters.solidworks.Archive.Construction.Assembly.AsmCandidate import (
    AsmCandidate,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import (
    MakePartTarget,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.ReadTargetBox import (
    ReadTargetBox,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)


# existing flat and ordered assemblies must become reusable generated definitions while sharing one actual child across repeated references
def MakeAsmTarget(ChildValue: AsmCandidate | OrderedAsm) -> TargetDocument:
    if type(ChildValue) not in (AsmCandidate, OrderedAsm):
        raise TypeError("an assembly target requires an actual complete SDK candidate")
    PartTarget = MakePartTarget(ChildValue.ChildValue)
    StateValue = ChildValue.StateValue
    ChildTargets = tuple(PartTarget for _ in ChildValue.OccurrenceValues)
    return TargetDocument(
        StateValue.RootValue,
        StateValue.ManagerValue,
        StateValue.CurrentConfig,
        ChildValue.HeaderValue,
        ChildValue.TopHeader,
        ChildValue.ManagerHeader,
        StateValue.FeatureValues,
        ReadTargetBox(StateValue.RootValue),
        ChildValue.OccurrenceValues,
        ChildTargets,
        len(ChildValue.OccurrenceValues),
        ChildValue.ConfigValue,
        ChildValue.ResolvedValue,
        ChildValue.StreamsValue,
        ChildValue.BytesValue,
    )
