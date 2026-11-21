from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# fresh selection must bind the complete actual first stock and cut history in one part
def CheckScopeOwner(
    CandidateValue: PartCandidate, StockValue: ThroughStock
) -> CutGraph:
    if (
        type(CandidateValue) is not PartCandidate
        or CandidateValue.PlanValue is not StockValue
    ):
        raise ValueError("selected stock differs from the actual generated part plan")
    CutValue = CandidateValue.CutValue
    if CutValue is None:
        raise ValueError("selected stock requires the actual ordinary through all cut")
    RootValue = RequireNode(CandidateValue.SystemValue.RootValue, "moPart_c")
    BossValue = RequireNode(CandidateValue.BossValue.FeatureValue, "moExtrusion_c")
    CutFeature = RequireNode(CutValue.FeatureValue, "moICE_c")
    if any(
        not isinstance(Value.ClassValue, RuntimeClass)
        or Value.ClassValue.SchemaValue != 1
        for Value in (RootValue, BossValue, CutFeature)
    ):
        raise ValueError(
            "selected stock requires its exact schema one model and feature owners"
        )
    if (
        BossValue.FieldsValue.get("owner") is not RootValue
        or CutFeature.FieldsValue.get("owner") is not RootValue
        or CandidateValue.ConfigValue.RootValue is not RootValue
    ):
        raise ValueError(
            "selected stock feature ownership differs from the actual part"
        )
    FeatureValues = (
        *CandidateValue.SystemValue.FeatureValues,
        CandidateValue.ProfileValue.ProfileValue,
        BossValue,
        CutValue.ProfileValue.ProfileValue,
        CutFeature,
    )
    if FeatureValues != CandidateValue.ResolvedValue.RootsValue:
        raise ValueError(
            "selected stock requires the complete unchanged first stock and cut history"
        )
    return CutValue
