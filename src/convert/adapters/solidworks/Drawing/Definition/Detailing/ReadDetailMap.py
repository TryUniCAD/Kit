from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailMap import (
    DetailMap,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailNode import (
    NeedDetailNode,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailRows import (
    NeedDetailRows,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedMapCount import (
    NeedMapCount,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.ReadDetailGroup import (
    ReadDetailGroup,
)


# proven native edge maps may be retained while portable child edge resolution stays explicit
def ReadDetailMap(ModelValue: ArchiveNode, VersionValue: int) -> DetailMap:
    if VersionValue != 19000:
        raise BodyUnsupported("drawing detailing index requires archive version 19000")
    _ = NeedDetailNode(ModelValue, "moDrawing_c")
    FieldsValue = ModelValue.FieldsValue
    GroupsValue = tuple(
        ReadDetailGroup(ItemValue)
        for ItemValue in NeedDetailRows(FieldsValue.get("f1570"))
    )
    NeedMapCount(FieldsValue, "n1578", len(GroupsValue))
    KeysValue = tuple(GroupValue.ModelKey for GroupValue in GroupsValue)
    if len(set(KeysValue)) != len(KeysValue):
        raise BodyUnsupported("drawing detailing index has duplicate model keys")
    return DetailMap(ModelValue, GroupsValue)
