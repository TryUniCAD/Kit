from copy import deepcopy as CopyDeep
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import (
    MakeNestedCase,
)


# malformed complete definition graphs must exercise real constructor admission without creating recorded native cases or synthetic archive nodes
def NestedFaultCase(FaultValue: str) -> dict[str, object]:
    Request = MakeNestedCase(True, r"C:\KitSdkNestedFaults")
    Definitions = CastValue(list[dict[str, object]], Request["definitions"])
    ModuleValue, RootValue = Definitions[-2:]
    ModuleRows = CastValue(list[dict[str, object]], ModuleValue["occurrences"])
    RootRows = CastValue(list[dict[str, object]], RootValue["occurrences"])
    if FaultValue == "cycle":
        ModuleRows[0]["target"] = "frame"
    elif FaultValue == "missing":
        RootRows[0]["target"] = "absent"
    elif FaultValue == "duplicate":
        Definitions[1]["id"] = Definitions[0]["id"]
    elif FaultValue == "unreachable":
        ExtraValue = CopyDeep(Definitions[0])
        ExtraValue["id"] = "unused"
        Definitions.append(ExtraValue)
    elif FaultValue == "foreign":
        RootRows[0]["hidden"] = True
    elif FaultValue == "name":
        RootRows[1]["occurrence"] = CopyDeep(RootRows[0]["occurrence"])
    elif FaultValue == "frame":
        CastValue(dict[str, object], RootRows[0]["occurrence"])["u"] = [0.0, 0.0, 0.0]
    else:
        raise ValueError("unknown declared nested constructor fault")
    return Request
