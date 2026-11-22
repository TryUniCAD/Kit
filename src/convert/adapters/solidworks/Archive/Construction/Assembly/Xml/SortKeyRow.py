from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native keyword grouping compares tag and decimal identifier strings independently of resolved feature traversal and allocation order
def SortKeyRow(RowValue: tuple[tuple[str, str], ArchiveNode]) -> tuple[str, str]:
    return RowValue[0][0], str(RowValue[1].FieldsValue["f08"])
