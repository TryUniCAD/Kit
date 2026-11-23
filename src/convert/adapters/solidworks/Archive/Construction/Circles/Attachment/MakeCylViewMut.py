from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakePartVis import (
    MakePartVis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.PartSelfView import (
    PartSelfView,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.PutSelfLookMut import (
    PutSelfLookMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)


# the attached radial child publishes its selected renderer and separate holder before final stream generation
def MakeCylViewMut(
    ChildValue: PartCandidate, LookValue: PartLookInput
) -> tuple[PartSelfView, dict[str, bytes]]:
    if type(LookValue) is not PartLookInput:
        raise ValueError("concentric child requires a typed named appearance")
    ViewValue = PartSelfView("<Default>_Display State 1", LookValue)
    PutSelfLookMut(ChildValue.SystemValue, ChildValue.DefinitionValue, ViewValue)
    StreamValue = MakePartVis(
        ChildValue.SystemValue,
        ChildValue.ProfileValue.ProfileValue,
        (ChildValue.HeaderValue, ChildValue.TopHeader),
        ChildValue.PlanValue,
        ViewValue,
    )
    return ViewValue, {KVisualStream: StreamValue}
