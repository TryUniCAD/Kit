from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# persistent feature identities must come from their typed node field without coercion
def NativeNodeId(NodeValue: ArchiveNode) -> int:
    NativeId = NodeValue.FieldsValue.get("f08")
    if type(NativeId) is not int or NativeId < 0:
        raise ValueError("typed model feature has no assigned persistent identity")
    return NativeId
