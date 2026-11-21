from downstream.lighting.AmbientInput import (
    AmbientInput,
)
from downstream.lighting.MakeAmbient import (
    MakeAmbient,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a single authored light belongs to the actual empty environment list without any owner update flag suppression
def AttachAmbientMut(
    RootValue: ArchiveNode,
    InputValue: AmbientInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    CreatedAt: int,
) -> ArchiveNode:
    RequireRootNode(RootValue, "moPart_c")
    FolderValue = ArchiveNode.RequireNode(RootValue.FieldsValue.get("f1e0"))
    RequireRootNode(FolderValue, "moEnvFolder_c")
    if FolderValue.FieldsValue.get("f60") != {
        "list": {"n": 0, "items": []},
        "tail": 0,
    }:
        raise ValueError("the authored ambient experiment requires an empty folder")
    NodeValue = MakeAmbient(
        FolderValue, InputValue, TargetValue, Allocator, CreatedAt
    )
    FolderValue.FieldsValue["f60"] = {
        "list": {"n": 1, "items": [{"o": NodeValue}]},
        "tail": 0,
    }
    return NodeValue
