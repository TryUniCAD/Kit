from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineFont import (
    MakeLineFont,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitFields import (
    MakeUnitFields,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeDimStyle(
    *, KindValue: str, FontName: str, LineStyleName: str
) -> dict[str, object]:
    AllowedKinds = {
        "base",
        "linear",
        "angle",
        "arc_length",
        "radial",
        "hole",
        "ordinate",
        "angular_ordinate",
        "chamfer",
        "diameter",
    }
    if KindValue not in AllowedKinds:
        raise ValueError(f"unsupported dimension style {KindValue!r}")
    FieldsValue: dict[str, object] = {
        "f08": 1,
        "fc": 1,
        "f10": 1,
        "f18": 1.0,
        "f20": 0.0127,
        "f28": 1,
        "f30": 1.0,
        "f38": 0.0127,
        "f40": 1,
        "f44": 0,
        "f48": "",
        "f50": "",
        "f58": 0.0,
        "f60": 0.0,
        "f68": 1,
        "f6c": 0,
        "f70": 1,
        "f74": 0,
        "f78": 0,
        "f80": 2,
        "f84": 3,
        "f88": 2,
        "f8c": 3,
        "f90": -1,
        "f94": 0,
        "f98": 0,
        "f9c": 0,
        "fc0": 1,
        "fe0": 192,
        "fd0": MakeLineFont(NameValue=LineStyleName),
        "fd8": MakeLineFont(NameValue=LineStyleName),
        "fe8": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
        "ff0": MakeUnitFields(KindValue="length", UnitCode=2, DecimalPlaces=2),
        "ff8": MakeUnitFields(KindValue="angle", UnitCode=0, DecimalPlaces=2),
    }
    if KindValue == "linear":
        FieldsValue.update({"f100": 2, "f104": 0, "f108": 0})
    elif KindValue == "angle":
        FieldsValue["f100"] = 322
    elif KindValue == "radial":
        FieldsValue.update({"f100": 2, "f104": 1})
    elif KindValue == "hole":
        FieldsValue.update({"f100": 0, "f94": 1})
    elif KindValue == "ordinate":
        FieldsValue.update({"f100": 1, "f104": 1, "f108": 0.0015875})
    elif KindValue == "angular_ordinate":
        FieldsValue.update(
            {"f100": 1, "f104": 21, "f108": 0, "f110": 0, "f114": 0, "f84": 2, "f8c": 2}
        )
    elif KindValue == "chamfer":
        FieldsValue.update(
            {
                "f100": 0,
                "f104": 1,
                "f108": 2,
                "f10c": 2,
                "f110": 0,
                "f118": 0.0,
                "f120": 0.0,
                "f128": 0,
                "f6c": 3,
                "f10": 2,
                "f94": 1,
            }
        )
    elif KindValue == "diameter":
        FieldsValue.update({"f100": 1, "f104": 0})
    return FieldsValue
