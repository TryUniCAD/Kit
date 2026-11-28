from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
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


# drawing folders require their own qualified class boundary and registration lifetimes instead of part system admission
def MakeDrawFolder(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    CreatedAt: int,
    Allocator: PersistentIds | None,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moDrawing_c")
    if ClassName not in (
        "moDocsFolder_c",
        "moCommentsFolder_c",
        "moInkMarkupFolder_c",
        "moBlockFolder_c",
        "moMarkupCommentFolder_c",
    ):
        raise ValueError(
            "drawing root folder class is outside the ordinary empty profile"
        )
    IsPersistent = ClassName not in ("moBlockFolder_c", "moMarkupCommentFolder_c")
    if IsPersistent != (Allocator is not None):
        raise ValueError(
            "drawing root folder allocator must follow its native registration lifetime"
        )
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(
        {
            "f360": int(ClassName != "moCommentsFolder_c"),
            "f370": 0,
            **FeatureTime(CreatedAt),
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
