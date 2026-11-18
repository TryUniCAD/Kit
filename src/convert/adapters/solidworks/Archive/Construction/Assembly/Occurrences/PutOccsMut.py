from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.JoinBoxes import (
    JoinBoxes,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeChildBox import (
    MakeChildBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlaceBox import (
    PlaceBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeDirectory import (
    MakeDirectory,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeOccConfig import (
    MakeOccConfig,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeOccurrence import (
    MakeOccurrence,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# occurrence publication derives directory users config reverse order direct counts and both bounds from the same actual generated placement sequence
def PutOccsMut(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
) -> tuple[ArchiveNode, ArchiveNode]:
    HeaderValue, TopHeader = HeadersValue
    OwnerFile = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f38"])
    Directory = MakeDirectory(ChildValue, len(Occurrences))
    ChildBounds = MakeChildBox(ChildValue)
    References = tuple(
        MakeOccurrence(
            StateValue,
            ChildValue,
            Directory,
            OwnerFile,
            ItemValue,
            InputValue.TargetValue,
            ChildBounds,
            OrdinalValue,
        )
        for OrdinalValue, ItemValue in enumerate(
            Occurrences, len(StateValue.FeatureValues) - 1
        )
    )
    BoundsValue = JoinBoxes(
        PlaceBox(ChildBounds, Occurrences[0].FrameValue),
        PlaceBox(ChildBounds, Occurrences[1].FrameValue),
    )
    RowsValue = [{"o": Reference} for Reference in References]
    StateValue.RootValue.FieldsValue.update(
        {
            "has_list68": 1,
            "f68": {"list": {"n": len(RowsValue), "items": RowsValue}, "tail": 0},
            "f1560": len(References),
            "has_f1a18": 1,
            "f1a18": BoundsValue,
            "has_f1a20": 1,
            "f1a20": dict(BoundsValue),
        }
    )
    StatesValue = [
        {"o": MakeOccConfig(Reference, StateValue.CurrentConfig)}
        for Reference in reversed(References)
    ]
    CurrentStates = StateValue.CurrentConfig.FieldsValue["fce8"]
    if not isinstance(CurrentStates, list):
        raise ValueError(
            "assembly configuration lost its actual component state collection"
        )
    CastValue(list[object], CurrentStates).extend(StatesValue)
    StateValue.CurrentConfig.FieldsValue.update(
        {"f4b0": len(References), "f85c": StateValue.Allocator.NextValue - 1}
    )
    DirectoryList = ArchiveNode(
        RuntimeClass("moExtObjectList_c", 1), {"items": (Directory,)}
    )
    for NodeValue in (HeaderValue, TopHeader):
        NodeValue.FieldsValue.update(
            {
                "f08": StateValue.Allocator.NextValue,
                "fc4": len(References),
                "f30": DirectoryList,
            }
        )
    return References[0], References[1]


from typing import cast as CastValue
