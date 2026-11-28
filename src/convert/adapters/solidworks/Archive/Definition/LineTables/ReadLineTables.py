from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Definition.LineTables.LineTableInput import (
    LineTableInput,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.OrderFontBinds import (
    OrderFontBinds,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.ReadFontBind import (
    ReadFontBind,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.ReadLinePattern import (
    ReadLinePattern,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)


# source table projection inverts the proved head insertion order without retaining archive objects or indices
def ReadLineTables(GraphValue: ModelDefGraph) -> LineTableInput:
    if (
        type(GraphValue) is not ModelDefGraph
        or type(CastValue(object, GraphValue.VersionValue)) is not int
        or GraphValue.VersionValue != 19000
        or GraphValue.DocumentValue.ClassValue != RuntimeClass("uiPartDoc_c", 1)
    ):
        raise ValueError("line tables require an ordinary current part Definition")
    FieldsValue = GraphValue.DocumentValue.FieldsValue
    StylesValue = RequireRecord(FieldsValue.get("f878"))
    FontValue = FieldsValue.get("f870")
    if (
        set(StylesValue) != {"n", "styles"}
        or not isinstance(FontValue, ArchiveNode)
        or FontValue.ClassValue != RuntimeClass("uiLineFontMgr_c", 1)
        or set(FontValue.FieldsValue) != {"n", "f10"}
    ):
        raise ValueError("line tables require their actual current managers")
    PatternRows = ReadRows(StylesValue["styles"])
    BindingRows = ReadRows(FontValue.FieldsValue["f10"])
    if (
        FieldInt(StylesValue, "n") != len(PatternRows)
        or FieldInt(FontValue.FieldsValue, "n") != len(BindingRows)
        or any(set(RowValue) != {"o"} for RowValue in PatternRows)
        or len({id(RowValue.get("o")) for RowValue in PatternRows}) != len(PatternRows)
        or len({id(RowValue.get("cfg")) for RowValue in BindingRows})
        != len(BindingRows)
    ):
        raise ValueError("line table counts or actual owned object identities differ")
    Patterns = tuple(ReadLinePattern(RowValue["o"]) for RowValue in PatternRows)
    Bindings = tuple(ReadFontBind(RowValue) for RowValue in BindingRows)
    InputValue = LineTableInput(Patterns, tuple(reversed(Bindings)))
    if OrderFontBinds(InputValue.BindingValues) != Bindings:
        raise ValueError(
            "source font map ordering is outside the native constructor profile"
        )
    return InputValue
