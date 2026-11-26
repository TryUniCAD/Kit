from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# system initialization clears native status bits while preserving unrelated constructor flags and leaving origin update scheduling separate
def ClearSystemMut(NodeValue: ArchiveNode) -> None:
    FlagsValue = NodeValue.FieldsValue.get("f0c")
    if type(FlagsValue) is not int:
        raise ValueError(
            "system feature initialization requires its actual native node flags"
        )
    NodeValue.FieldsValue["f0c"] = FlagsValue & 0xFFFD7FF8
