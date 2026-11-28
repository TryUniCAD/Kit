from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# visibility attribute references share only the actual state scope and generated object identity
def MakeVisRow(KeyValue: int, *Values: ArchiveNode) -> dict[str, object]:
    return {"key": KeyValue, "objs": [{"o": NodeValue} for NodeValue in Values]}
