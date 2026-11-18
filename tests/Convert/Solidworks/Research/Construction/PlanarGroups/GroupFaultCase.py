from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import (
    GroupCaseInput,
)


# malformed complete neutral groups must exercise constructor ownership and measured profile limits instead of patching a saved or already generated graph
def GroupFaultCase(FaultValue: str) -> dict[str, object]:
    RequestValue = GroupCaseInput(3, True)
    MatesValue = CastValue(list[dict[str, object]], RequestValue["mates"])
    EndValues = CastValue(list[dict[str, object]], MatesValue[0]["endpoints"])
    if FaultValue == "missing_endpoint":
        EndValues[0]["occurrence"] = 3
    elif FaultValue == "same_occurrence":
        EndValues[0]["occurrence"] = EndValues[1]["occurrence"]
    elif FaultValue == "cross_axis":
        EndValues[0]["axis"] = "x"
    elif FaultValue == "same_name":
        MatesValue[0]["name"] = MatesValue[1]["name"]
    elif FaultValue == "zero_distance":
        MatesValue[1]["distance_m"] = 0.0
    elif FaultValue == "wrong_distance":
        MatesValue[1]["distance_m"] = 0.0123
    elif FaultValue == "fixed_missing":
        RequestValue["fixed_occurrence"] = 3
    elif FaultValue == "extra_state":
        MatesValue[0]["suppressed"] = True
    else:
        raise ValueError("unknown declared planar group admission fault")
    return RequestValue
