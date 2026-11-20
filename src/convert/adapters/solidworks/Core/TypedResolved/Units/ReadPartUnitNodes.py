from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KUnitClasses,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# document unit choices must come from the actual complete user table and its concrete class owners
def ReadUnitNodes(RootValue: ArchiveNode) -> dict[str, ArchiveNode]:
    TableValue = RequireNode(RootValue.FieldsValue["f9b8"], "moUnitsTable_c")
    Entries = ReadRows(TableValue.FieldsValue["items"])
    ClassNames = tuple(KUnitClasses.values())
    if len(Entries) != FieldInt(TableValue.FieldsValue, "n") or len(Entries) != len(
        ClassNames
    ):
        raise ValueError("document units require the complete current table")
    return {
        RoleValue: RequireNode(RowValue["o"], ClassName)
        for (RoleValue, ClassName), RowValue in zip(
            KUnitClasses.items(), Entries, strict=True
        )
    }
