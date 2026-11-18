from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetHeightMut import (
    SetHeightMut,
)


# the concrete label defaults bind their own standard field and preserve independent root label options
def SetLabelsMut(FieldsValue: MutableMapping[str, object]) -> None:
    SetHeightMut(FieldsValue, "f458")
    for FieldName in ("fe8", "f18", "f1e8", "f2b8", "f388"):
        LabelValue = ReadFields(FieldsValue, FieldName)
        LabelValue["f44"] = 0
        for FormatName in ("f98", "fa8", "fc0", "fb0", "fb8", "fa0"):
            SetHeightMut(LabelValue, FormatName)
    ReadFields(FieldsValue, "fe8").update({"f2c": 1, "fe4": 0})
    ReadFields(FieldsValue, "f1e8").update({"fc": 2, "fc8": 0, "f58": 1})
