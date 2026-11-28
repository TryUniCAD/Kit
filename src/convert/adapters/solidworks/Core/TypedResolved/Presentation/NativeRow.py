from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.SystemState import (
    ReadSystemState,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# persisted tree rows retain real native identities and owner containment independently from modeling dependencies
def MakeNativeRow(
    LinkValue: NativeLink,
    NodeValue: ArchiveNode,
    ParentValue: ArchiveNode | None = None,
    RoleValue: str | None = None,
) -> Mapping[str, object]:
    NativeId = NativeNodeId(NodeValue)
    ClassName = NodeValue.ClassValue.NameValue
    return {
        "id": f"sldprt:feature:{NativeId}",
        "native_object_id": NativeId,
        "name": ReadNativeName(NodeValue),
        "type": ClassName.removeprefix("mo").removesuffix("_c"),
        "class": ClassName,
        "parent_id": (
            f"sldprt:feature:{NativeNodeId(ParentValue)}"
            if ParentValue is not None
            else None
        ),
        "parent": ReadNativeName(ParentValue) if ParentValue is not None else None,
        "owner_role": RoleValue,
        "source": "persisted",
        "typed_archive_owner": NativeNodeSpan(LinkValue, NodeValue),
        "state": ReadSystemState(NodeValue.FieldsValue),
    }
