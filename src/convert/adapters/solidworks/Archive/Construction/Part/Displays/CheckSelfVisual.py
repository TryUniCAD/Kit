from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakePartVis import (
    MakePartVis,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)


# an optional planar child store must agree with the actual constructor intent and live child graph
def CheckSelfVisual(ChildValue: PartCandidate) -> None:
    StoredValue = ChildValue.StreamsValue.get(KVisualStream)
    ViewValue = ChildValue.SelfView
    if ViewValue is None:
        if StoredValue is not None:
            raise ValueError(
                "planar child visual store has no modeled appearance association"
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
        raise ValueError("planar child visual store does not match its model owners")
