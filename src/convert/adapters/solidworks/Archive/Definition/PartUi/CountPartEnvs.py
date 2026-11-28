from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.PartUi.RequirePartUi import (
    RequirePartUi,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# environment count is the actual dynamic collection length while its window semantics remain separately unprojected
def CountPartEnvs(GraphValue: ModelDefGraph) -> int:
    FieldsValue = RequirePartUi(GraphValue)
    CountValue = FieldInt(FieldsValue, "nenv")
    RowsValue = ReadRows(FieldsValue.get("faf8"))
    if (
        not 0 <= CountValue <= 0xFFFF
        or CountValue != len(RowsValue)
        or any(set(RowValue) != {"o"} for RowValue in RowsValue)
        or len({id(RowValue.get("o")) for RowValue in RowsValue}) != CountValue
    ):
        raise ValueError("part ui environment count or owned collection differs")
    for RowValue in RowsValue:
        OwnerValue = RowValue["o"]
        if not isinstance(
            OwnerValue, ArchiveNode
        ) or OwnerValue.ClassValue != RuntimeClass("uiUserModelEnv_c", 1):
            raise ValueError("part ui environment requires its actual current owner")
    return CountValue
