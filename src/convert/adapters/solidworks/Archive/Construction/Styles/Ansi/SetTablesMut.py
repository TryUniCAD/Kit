from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetHeightMut import (
    SetHeightMut,
)


# every table subtype reaches the same standard and text height setters with its own receiver
def SetTablesMut(FieldsValue: MutableMapping[str, object]) -> None:
    FieldsValue["f08"] = 0
    SetHeightMut(FieldsValue, "f328")
    for FieldName in (
        "f10",
        "f2e0",
        "f50",
        "fb0",
        "f110",
        "f150",
        "f1d0",
        "f218",
        "f268",
    ):
        TableValue = ReadFields(FieldsValue, FieldName)
        TableValue["f2c"] = 0
        SetHeightMut(TableValue, "f10")
