from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import (
    FontBinding,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    RequireRecord,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# current source bindings retain named font selectors and reject every unmodeled width or font field
def ReadFontBind(RowValue: Mapping[str, object]) -> FontBinding:
    ConfigValue = RowValue.get("cfg")
    if (
        set(RowValue) != {"key", "cfg"}
        or not isinstance(ConfigValue, ArchiveNode)
        or ConfigValue.ClassValue != RuntimeClass("uiLFConfig_c", 1)
        or set(ConfigValue.FieldsValue) != {"f08", "f10", "f18"}
    ):
        raise ValueError("line font binding requires its concrete current record")
    FieldsValue = ConfigValue.FieldsValue
    WidthValue = RequireRecord(FieldsValue["f10"])
    if set(WidthValue) != {"f06", "f00"} or RequireScalar(WidthValue["f00"]) != -1.0:
        raise ValueError("custom or unrepresented line font width is unsupported")
    return FontBinding(
        FieldText(RowValue, "key"),
        FieldText(FieldsValue, "f08"),
        FieldInt(WidthValue, "f06"),
        FieldInt(FieldsValue, "f18"),
    )
