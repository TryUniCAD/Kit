from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)


# keyword rows index the actual environment membership without adding duplicate resolved roots
def AsmKeyNodes(
    RootValue: ArchiveNode, FeaturesValue: tuple[ArchiveNode, ...]
) -> tuple[ArchiveNode, ...]:
    EnvironmentValue = RequireNode(RootValue.FieldsValue.get("f1e0"), "moEnvFolder_c")
    if (
        EnvironmentValue.FieldsValue.get("owner") is not RootValue
        or sum(NodeValue is EnvironmentValue for NodeValue in FeaturesValue) != 1
    ):
        raise ValueError("assembly keys require the actual resolved environment root")
    MembersValue = ReadChildren(EnvironmentValue)
    if any(
        NodeValue.FieldsValue.get("owner") is not EnvironmentValue
        for NodeValue in MembersValue
    ):
        raise ValueError("assembly keyword light has a different environment owner")
    if any(
        NodeValue.ClassValue.NameValue not in ("moAmbientLight_c", "moDirectionLight_c")
        for NodeValue in MembersValue
    ):
        raise ValueError("assembly keyword environment contains an unsupported member")
    NodesValue = (*FeaturesValue, *MembersValue)
    if len({FieldInt(NodeValue.FieldsValue, "f08") for NodeValue in NodesValue}) != len(
        NodesValue
    ):
        raise ValueError("assembly keyword rows contain duplicate feature identities")
    return NodesValue
