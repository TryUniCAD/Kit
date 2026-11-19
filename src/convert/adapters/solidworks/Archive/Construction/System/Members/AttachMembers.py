from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import (
    MemberInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberGraph import (
    MemberGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import (
    MakeLightMut,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeNotesMut import (
    MakeNotesMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# populated system owners must share the real model allocator and retain source entry order
def AttachMembers(
    SystemValue: PartSystem,
    InputValue: MemberInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> MemberGraph:
    if type(SystemValue) is not PartSystem or type(InputValue) is not MemberInput:
        raise TypeError(
            "member attachment requires actual system and typed semantic input"
        )
    RequireRootNode(SystemValue.RootValue, "moPart_c")
    if (
        len(SystemValue.ConfigValues) != 1
        or SystemValue.ManagerValue.FieldsValue.get("f360")
        is not SystemValue.ConfigValues[0]
        or SystemValue.ManagerValue.FieldsValue.get("f368")
        is not SystemValue.ConfigValues[0]
    ):
        raise ValueError(
            "member construction requires one actual selected configuration"
        )
    Cabinet = SystemValue.SystemValues.CabinetValue
    Folder = SystemValue.SystemValues.FolderValues["moEnvFolder_c"]
    if any(
        sum(ValueInput is OwnerValue for ValueInput in SystemValue.FeatureValues) != 1
        for OwnerValue in (Cabinet, Folder)
    ):
        raise ValueError("members require the actual registered system roots")
    if SystemValue.RootValue.FieldsValue.get("f1e0") is not Folder:
        raise ValueError("environment must be the actual part configuration owner")
    for OwnerValue in (Cabinet, Folder):
        if OwnerValue.FieldsValue.get(
            "owner"
        ) is not SystemValue.RootValue or OwnerValue.FieldsValue.get("f60") != {
            "list": {"n": 0, "items": []},
            "tail": 0,
        }:
            raise ValueError("members require actual empty system owner lists")
    NamesValue = tuple(
        ReadNodeName(NodeValue)
        for NodeValue, FieldName in Allocator.Allocations
        if FieldName == "f08" and "f2b0" in NodeValue.FieldsValue
    )
    MemberNames = (
        InputValue.NotesValue.HeadName,
        InputValue.NotesValue.EndName,
        *(ValueInput.NameValue for ValueInput in InputValue.LightValues),
    )
    if set(NamesValue).intersection(MemberNames):
        raise ValueError("member captions collide with actual existing system nodes")
    LightsValue = tuple(
        MakeLightMut(Folder, ValueInput, TargetValue, Allocator)
        for ValueInput in InputValue.LightValues
    )
    NotesValue = MakeNotesMut(Cabinet, InputValue.NotesValue, TargetValue, Allocator)
    for OwnerValue, NodesValue in (
        (Folder, LightsValue),
        (Cabinet, (NotesValue.HeadValue, NotesValue.EndValue)),
    ):
        OwnerValue.FieldsValue["f60"] = {
            "list": {
                "n": len(NodesValue),
                "items": [{"o": ValueInput} for ValueInput in NodesValue],
            },
            "tail": 0,
        }
    return MemberGraph(NotesValue, LightsValue)
