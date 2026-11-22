from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.XmlWalkState import (
    XmlWalkState,
)


# xml closure must visit each actual definition once while allocating every direct placement and retaining dependency before owner model order
def VisitXmlMut(StateValue: XmlWalkState, TargetValue: TargetDocument) -> int:
    IdentityValue = id(TargetValue.RootValue)
    if IdentityValue in StateValue.NodeIds:
        return StateValue.NodeIds[IdentityValue][0]
    ModelId, FileId = StateValue.NextValue, StateValue.NextValue + 1
    StateValue.NextValue += 2
    StateValue.NodeIds[IdentityValue] = ModelId, FileId
    StateValue.FileValues.append(TargetValue)
    RowsValue = StateValue.RefValues[IdentityValue] = []
    for Reference, ChildValue in zip(
        TargetValue.ReferenceValues, TargetValue.ChildTargets, strict=True
    ):
        ReferenceId = StateValue.NextValue
        StateValue.NextValue += 1
        ChildId = VisitXmlMut(StateValue, ChildValue)
        RowsValue.append((ReferenceId, Reference, ChildId))
    StateValue.ModelValues.append(TargetValue)
    return ModelId
