from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeOccConfig import (
    MakeOccConfig,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.PlacedBounds import (
    PlacedBounds,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# direct storage rows and recursively expanded activity must be published separately while both headers and parent boxes remain model derived
def PublishRefsMut(
    StateValue: AssemblyState,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    Placements: tuple[TargetPlacement, ...],
    References: tuple[ArchiveNode, ...],
) -> None:
    BoundsValue = PlacedBounds(Placements)
    ActivityValue = sum(
        1 + ItemValue.TargetValue.ActivityValue for ItemValue in Placements
    )
    StateValue.RootValue.FieldsValue.update(
        {
            "has_list68": 1,
            "f68": {
                "list": {
                    "n": len(References),
                    "items": [{"o": Reference} for Reference in References],
                },
                "tail": 0,
            },
            "f1560": len(References),
            "has_f1a18": 1,
            "f1a18": BoundsValue,
            "has_f1a20": 1,
            "f1a20": dict(BoundsValue),
        }
    )
    CurrentStates = StateValue.CurrentConfig.FieldsValue["fce8"]
    if not isinstance(CurrentStates, list):
        raise ValueError("assembly configuration lost its component state list")
    CastValue(list[object], CurrentStates).extend(
        {"o": MakeOccConfig(Reference, StateValue.CurrentConfig)}
        for Reference in reversed(References)
    )
    StateValue.CurrentConfig.FieldsValue.update(
        {"f4b0": ActivityValue, "f85c": StateValue.Allocator.NextValue - 1}
    )
    Directories = {
        id(Reference.FieldsValue["f3b0"]): Reference.FieldsValue["f3b0"]
        for Reference in References
    }
    DirectoryList = ArchiveNode(
        RuntimeClass("moExtObjectList_c", 1), {"items": tuple(Directories.values())}
    )
    for NodeValue in HeadersValue:
        NodeValue.FieldsValue.update(
            {
                "f08": StateValue.Allocator.NextValue,
                "fc4": ActivityValue,
                "f30": DirectoryList,
            }
        )
