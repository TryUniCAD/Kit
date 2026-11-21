from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetHeightMut import (
    SetHeightMut,
)


# annotation defaults apply actual base records after the root bend setter and retain unrelated authored state
def SetAnnoStyleMut(FieldsValue: MutableMapping[str, object]) -> None:
    FieldsValue.update({"f10": 0, "f14": 1, "f1c": 1, "f20": 3, "f24": 1})
    for FieldName in (
        "f40",
        "fa0",
        "f108",
        "f178",
        "f1e8",
        "f250",
        "f2c0",
        "f398",
        "f418",
        "f4a0",
    ):
        AnnotationValue = ReadFields(FieldsValue, FieldName)
        AnnotationValue.update({"f8": 0, "f24": 1})
        SetHeightMut(AnnotationValue, "f50")
    ReadFields(FieldsValue, "f2c0")["f24"] = 0
    ReadFields(FieldsValue, "f418")["f5c"] = 0
