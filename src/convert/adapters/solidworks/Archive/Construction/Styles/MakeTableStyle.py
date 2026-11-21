from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeTableStyle(*, KindValue: str, FontName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": 0,
        "f0c": -1,
        "f28": 0,
        "f2c": 1,
        "f38": 0,
        "f18": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f20": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f10": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
    }
    if KindValue in ("general", "title_block"):
        pass
    elif KindValue == "revision":
        FieldsValue.update(
            {"f40": 0, "f44": 0, "f48": 1, "f4c": 0, "f50": "", "f58": 0}
        )
    elif KindValue == "bom":
        FieldsValue.update({"f40": 0, "f48": "", "f50": "", "f58": ""})
    elif KindValue == "hole":
        FieldsValue.update(
            {
                "f40": 0,
                "f44": 0,
                "f48": 0.008,
                "f50": 0.78539816339745,
                "f58": 0,
                "f5c": 0,
                "f60": 2,
                "f64": 2,
                "f68": 1,
                "f6c": 1,
                "f70": 1,
                "f74": 0,
                "f78": 0,
                "f7c": 0,
            }
        )
    elif KindValue in ("weld", "family"):
        FieldsValue["f40"] = 0
    elif KindValue == "bend":
        FieldsValue.update({"f40": 2, "f44": 2, "f48": 2, "f4c": 0})
    elif KindValue == "punch":
        FieldsValue.update(
            {
                "f40": 0,
                "f44": 0,
                "f48": 0,
                "f4c": 0,
                "f50": 0,
                "f58": 0.008,
                "f60": 0.78539816339745,
                "f68": 1,
                "f6c": 2,
                "f70": 2,
            }
        )
    else:
        raise ValueError(f"unsupported table style {KindValue!r}")
    return FieldsValue
