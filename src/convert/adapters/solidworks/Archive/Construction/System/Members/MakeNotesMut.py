from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesGraph import (
    NotesGraph,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import (
    MakeFeatTime,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the pair must derive its markers and reciprocal ownership from actual allocated nodes
def MakeNotesMut(
    OwnerValue: ArchiveNode,
    InputValue: NotesInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> NotesGraph:
    RequireRootNode(OwnerValue, "moDetailCabinet_c")
    if type(InputValue) is not NotesInput:
        raise TypeError("notes construction requires typed pair intent")
    NodesValue: list[ArchiveNode] = []
    for NameValue, CreatedValue, IsHead in (
        (InputValue.HeadName, InputValue.HeadCreated, True),
        (InputValue.EndName, InputValue.EndCreated, False),
    ):
        NodeValue = ArchiveNode(RuntimeClass("moNotesAreaFtrFolder_c", 1), {})
        InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
        NodeValue.FieldsValue.update(
            {
                "f360": 1,
                "f370": 0,
                "f378": 1,
                "f37c": int(IsHead),
                "f388": None,
                "f394": 0,
                "f39c": 1,
            }
        )
        NodeValue.FieldsValue.update(MakeFeatTime(CreatedValue))
        ClearSystemMut(NodeValue)
        NodesValue.append(NodeValue)
    HeadValue, EndValue = NodesValue
    HeadValue.FieldsValue["f388"] = EndValue
    EndValue.FieldsValue["f388"] = HeadValue
    return NotesGraph(HeadValue, EndValue)
