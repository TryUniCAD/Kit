from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeAnnoStyle(
    *, KindValue: str, FontName: str, LanguageId: int
) -> dict[str, object]:
    if type(CastValue(object, LanguageId)) is not int or not 0 <= LanguageId <= 65535:
        raise ValueError("language id must be an authored Windows language id")
    FieldsValue: dict[str, object] = {
        "f8": 1,
        "f10": 0.00625,
        "f18": 1,
        "f1c": 2 if LanguageId & 1023 == 13 else 0,
        "f20": 0,
        "f24": 0,
        "f28": 0,
        "f34": 0,
        "f40": 0,
        "f44": -1,
        "f2c": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f38": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f50": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
    }
    if KindValue == "cloud":
        FieldsValue["f58"] = 0.00508
    elif KindValue == "weld":
        FieldsValue.update(
            {
                "f58": 0,
                "f60": MakeCharFormat(
                    FontName=FontName, HeightValue=0.00212, PointHeight=0
                ),
            }
        )
    elif KindValue == "surface_finish":
        FieldsValue.update({"f58": 0, "f5c": 2, "f60": 1.0, "f68": 1.0})
    elif KindValue == "bend":
        FieldsValue.update({"f58": 0, "f5c": 0, "f60": 0, "f68": 0.01016})
    elif KindValue == "gtol":
        FieldsValue.update({"f58": 1, "f5c": 1, "f60": 46})
    elif KindValue == "datum":
        FieldsValue.update({"f58": 0, "f5c": 0, "f60": 1, "f64": 0, "f68": 1, "f6c": 0})
    elif KindValue == "balloon":
        FieldsValue.update(
            {
                "f58": 2,
                "f5c": 2,
                "f60": 1,
                "f64": 1,
                "f68": 1,
                "f6c": 2,
                "f70": "",
                "f78": "",
                "f80": 1,
                "f88": 0.01016,
                "f90": 0.01016,
                "f98": 0.0,
                "fa0": 0.0,
                "fa8": 0.001,
                "fb0": 0,
                "fb4": 0,
                "fb8": 1,
                "fc0": "X",
            }
        )
    elif KindValue == "view_location":
        FieldsValue.update(
            {
                "f58": 7,
                "f5c": 9,
                "f60": 11,
                "f64": 2,
                "f68": 0.01016,
                "f70": 1,
                "f74": 0,
                "f78": 0.0,
            }
        )
    elif KindValue == "note":
        FieldsValue.update(
            {
                "f58": 0,
                "f5c": 10,
                "f60": 0,
                "f68": 0.01016,
                "f70": 0.0,
                "f78": 0.001,
                "f80": 1,
            }
        )
    elif KindValue != "base":
        raise ValueError(f"unsupported annotation style {KindValue!r}")
    return FieldsValue
