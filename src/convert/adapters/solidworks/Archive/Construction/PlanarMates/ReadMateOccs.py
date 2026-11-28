from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# each direct component must be an actual distinct member of the containing assembly before any ordered mate allocation begins
def ReadMateOccs(AssemblyValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    ListValue = RequireRecord(
        RequireRecord(AssemblyValue.FieldsValue.get("f68")).get("list")
    )
    ItemsValue = ReadRows(ListValue.get("items"))
    Occurrences = tuple(
        RequireNode(Value.get("o"), "moReference_c") for Value in ItemsValue
    )
    if (
        len(Occurrences) < 2
        or FieldInt(ListValue, "n") != len(Occurrences)
        or FieldInt(AssemblyValue.FieldsValue, "f1560") != len(Occurrences)
        or len({id(Value) for Value in Occurrences}) != len(Occurrences)
        or any(
            Value.FieldsValue.get("owner") is not AssemblyValue for Value in Occurrences
        )
    ):
        raise ValueError(
            "mate construction requires the complete actual direct component list"
        )
    return Occurrences
