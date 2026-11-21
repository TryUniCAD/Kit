from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetHeightMut import (
    SetHeightMut,
)


# concrete subtype predicates select the ansi base setters before each subtype performs its own defaults
def SetDimensionMut(FieldsValue: MutableMapping[str, object], KindValue: str) -> None:
    IsAngular = KindValue in ("angle", "angular_ordinate")
    FieldsValue.update({"f08": 0, "f84": 2, "f88": 2 if IsAngular else 3, "f8c": 2})
    FieldsValue["f6c"] = (
        2 if KindValue == "angular_ordinate" else 0 if KindValue == "chamfer" else 1
    )
    FlagsValue = FieldsValue["fe0"]
    if type(FlagsValue) is not int:
        raise TypeError("dimension flags must be an actual integer")
    FieldsValue["fe0"] = FlagsValue | 0x200
    SetHeightMut(FieldsValue, "fe8")
    if IsAngular:
        FieldsValue["f80"] = 2
    if KindValue == "linear":
        FieldsValue.update({"f100": 1, "f104": 0})
        WordValue = FieldsValue["f108"]
        if type(WordValue) is not int:
            raise TypeError("linear dimension options must be an actual integer")
        FieldsValue["f108"] = (WordValue | 0x20) & ~0x10
    elif KindValue == "angular_ordinate":
        FieldsValue["f100"] = 0
