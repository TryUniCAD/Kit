from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)


# cold naming must never replace prior body ownership selected outputs or a previously transmitted geometry cache
def CheckColdFresh(CandidateValue: PartCandidate) -> dict[str, object]:
    ModelValue = RequireNode(CandidateValue.SystemValue.RootValue, "moPart_c")
    BossValue = RequireNode(CandidateValue.BossValue.FeatureValue, "moExtrusion_c")
    if type(CandidateValue.PlanValue) is not BlindPlan:
        raise ValueError("cold naming requires the ordinary rectangular boss plan")
    Vertices = CandidateValue.PlanValue.VerticesValue
    if len(Vertices) != 4 or any(
        len({PointValue[AxisValue] for PointValue in Vertices}) != 2
        for AxisValue in (0, 1)
    ):
        raise ValueError("cold naming requires its complete axis aligned rectangle")
    Expected = (
        *CandidateValue.SystemValue.FeatureValues,
        CandidateValue.ProfileValue.ProfileValue,
        BossValue,
    )
    if len(Expected) != len(CandidateValue.ResolvedValue.RootsValue) or any(
        LeftValue is not RightValue
        for LeftValue, RightValue in zip(
            Expected, CandidateValue.ResolvedValue.RootsValue, strict=True
        )
    ):
        raise ValueError("cold naming requires the actual unchanged ordinary history")
    ManagerValue = ModelValue.FieldsValue.get("fd88")
    if not isinstance(ManagerValue, dict):
        raise ValueError("cold naming requires a mutable actual atom manager")
    Manager = CastValue(dict[str, object], ManagerValue)
    if Manager.get("n6c") != 0 or Manager.get("atoms") or Manager.get("fa8") != 0:
        raise ValueError("cold naming cannot replace a populated or old atom manager")
    GhostValue = RequireRecord(ModelValue.FieldsValue.get("fd90"))
    if GhostValue.get("n") != 0 or GhostValue.get("objects"):
        raise ValueError("cold naming cannot replace retained ghost bodies")
    if (
        any(
            FieldInt(BossValue.FieldsValue, FieldName) != 0
            for FieldName in ("has_f528", "has_f530", "n494")
        )
        or BossValue.FieldsValue.get("f538") is not None
        or BossValue.FieldsValue.get("f498")
    ):
        raise ValueError("cold naming requires a fresh actual boss output")
    if any("Partition" in NameValue for NameValue in CandidateValue.StreamsValue):
        raise ValueError("cold naming cannot attach to transmitted kernel geometry")
    return Manager
