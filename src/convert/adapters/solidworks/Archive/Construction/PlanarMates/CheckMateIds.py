from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# persistent allocation must agree with the actual parent publication boundary before any mate state changes
def CheckMateIds(Context: MateContext, Occurrences: tuple[ArchiveNode, ...]) -> None:
    NodesValue = (
        Context.AssemblyValue,
        Context.GroupValue,
        Context.HeaderValue,
        Context.ConfigValue,
        *Occurrences,
    )
    if any(
        not isinstance(Value.ClassValue, RuntimeClass)
        or Value.ClassValue.SchemaValue != 1
        for Value in NodesValue
    ):
        raise ValueError("mate construction requires schema one owned graph roots")
    NextValue = Context.Allocator.NextValue
    Identifiers = tuple(
        FieldInt(Value.FieldsValue, "f08")
        for Value in (Context.GroupValue, *Occurrences)
    )
    if (
        NextValue != FieldInt(Context.HeaderValue.FieldsValue, "f08")
        or any(not 0 <= Value < NextValue for Value in Identifiers)
        or len(set(Identifiers)) != len(Identifiers)
        or FieldInt(Context.HeaderValue.FieldsValue, "fc4") != len(Occurrences)
        or FieldInt(Context.ConfigValue.FieldsValue, "f4b0") != len(Occurrences)
    ):
        raise ValueError("mate allocator and parent occurrence publication differ")
