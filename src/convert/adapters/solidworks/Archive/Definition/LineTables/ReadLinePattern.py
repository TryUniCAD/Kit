from convert.adapters.solidworks.Archive.Definition.LineTables.LinePattern import (
    LinePattern,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadRows,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# native pattern records qualify only when their actual class fields and segment count are fully represented
def ReadLinePattern(Value: object) -> LinePattern:
    if (
        not isinstance(Value, ArchiveNode)
        or Value.ClassValue != RuntimeClass("moLineStyle_c", 1)
        or set(Value.FieldsValue) != {"f08", "f10", "f18", "nseg", "f20"}
    ):
        raise ValueError("line pattern requires its concrete current record")
    FieldsValue = Value.FieldsValue
    Segments = ReadRows(FieldsValue["f18"])
    FlagValue = FieldInt(FieldsValue, "f20")
    if FieldInt(FieldsValue, "nseg") != len(Segments) or FlagValue not in (0, 1):
        raise ValueError("line pattern count or thick thin mode is unrepresented")
    if any(set(RowValue) != {"seg"} for RowValue in Segments):
        raise ValueError("line pattern segment has unrepresented fields")
    return LinePattern(
        FieldText(FieldsValue, "f08"),
        FieldText(FieldsValue, "f10"),
        tuple(RequireScalar(RowValue["seg"]) for RowValue in Segments),
        bool(FlagValue),
    )
