from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# directory traversal preserves the actual nodes owned by the standalone header
def ReadHeadItems(Directory: ArchiveNode) -> tuple[ArchiveNode, ...]:
    Items = Directory.FieldsValue["items"]
    if not isinstance(Items, tuple):
        raise ValueError("SOLIDWORKS direct header directory requires ordered items")
    return tuple(
        ArchiveNode.RequireNode(ItemValue)
        for ItemValue in CastValue(tuple[object, ...], Items)
    )
