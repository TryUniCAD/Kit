from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakePartVis import (
    MakePartVis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PlanLookIds import (
    PlanLookIds,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import (
    ReadEmptyMgrs,
)
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)


# an optional child visual store must agree with the actual constructor intent and live child graph
def CheckSelfVisual(ChildValue: PartCandidate) -> None:
    ViewRole = "concentric" if type(ChildValue.PlanValue) is CirclePlan else "planar"
    StoredValue = ChildValue.StreamsValue.get(KVisualStream)
    ViewValue = ChildValue.SelfView
    if ViewValue is None:
        if StoredValue is not None:
            raise ValueError(
                f"{ViewRole} child visual store has no modeled appearance association"
            )
        return
    Predicted = MakePartVis(
        ChildValue.SystemValue,
        ChildValue.ProfileValue.ProfileValue,
        (ChildValue.HeaderValue, ChildValue.TopHeader),
        ChildValue.PlanValue,
        ViewValue,
    )
    if Predicted != StoredValue:
        raise ValueError(
            f"{ViewRole} child visual store does not match its model owners"
        )
    RenderValue = ViewValue.AppearanceValue
    if type(RenderValue) is PartLookInput:
        _, _, StateValue = PlanLookIds(RenderValue)
        if ReadEmptyMgrs(ChildValue.DefinitionValue) != StateValue:
            raise ValueError(
                f"{ViewRole} child visual store requires its actual independent appearance allocator"
            )
