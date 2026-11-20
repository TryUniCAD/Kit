from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)


# keyword rows must index the actual system members without duplicating resolved roots
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
    Cabinets = tuple(
        NodeValue
        for NodeValue in FeaturesValue
        if NodeValue.ClassValue.NameValue == "moDetailCabinet_c"
    )
    if len(Cabinets) != 1 or Cabinets[0].FieldsValue.get("owner") is not RootValue:
        raise ValueError("assembly keys require the actual resolved annotation cabinet")
    CabinetValue = Cabinets[0]
    NotesValue = ReadChildren(CabinetValue)
    if any(
        NodeValue.ClassValue.NameValue == "moNotesAreaFtrFolder_c"
        for NodeValue in FeaturesValue
    ) or any(
        NodeValue.FieldsValue.get("owner") is not CabinetValue
        for NodeValue in NotesValue
    ):
        raise ValueError("assembly keyword notes must belong only to the cabinet")
    if NotesValue:
        _ = ReadNotesInput(NotesValue)
    NodesValue = (*FeaturesValue, *MembersValue, *NotesValue)
    if len({FieldInt(NodeValue.FieldsValue, "f08") for NodeValue in NodesValue}) != len(
        NodesValue
    ):
        raise ValueError("assembly keyword rows contain duplicate feature identities")
    return NodesValue
