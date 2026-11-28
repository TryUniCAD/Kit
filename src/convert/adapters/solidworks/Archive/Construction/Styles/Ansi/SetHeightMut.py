from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)


# the native system height setter stores metres and clears point height mode without changing authored typography
def SetHeightMut(FieldsValue: MutableMapping[str, object], FieldName: str) -> None:
    FormatValue = ReadFields(FieldsValue, FieldName)
    FormatValue["f10"] = 0.003175
    FormatValue["f18"] = 0
