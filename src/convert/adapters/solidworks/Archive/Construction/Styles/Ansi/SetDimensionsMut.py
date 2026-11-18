from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetDimensionMut import (
    SetDimensionMut,
)


# the native root visits all ten concrete dimension records after its scalar ansi defaults
def SetDimensionsMut(FieldsValue: MutableMapping[str, object]) -> None:
    FieldsValue.update(
        {"f68": 0, "f20": 0.00127, "f28": 0.003175, "f38": 0.0127, "f64": 1}
    )
    for FieldName, KindValue in (
        ("fe0", "linear"),
        ("f1f0", "angle"),
        ("f2f8", "arc_length"),
        ("f3f8", "radial"),
        ("f500", "hole"),
        ("f608", "ordinate"),
        ("f718", "angular_ordinate"),
        ("f830", "chamfer"),
        ("f960", "diameter"),
        ("fa68", "base"),
    ):
        SetDimensionMut(ReadFields(FieldsValue, FieldName), KindValue)
    for FieldName in ("fe0", "f1f0", "f2f8"):
        DimensionValue = ReadFields(FieldsValue, FieldName)
        WordValue = DimensionValue["fe0"]
        if type(WordValue) is not int:
            raise TypeError("dimension flags must be an actual integer")
        DimensionValue["fe0"] = WordValue | 0x400
