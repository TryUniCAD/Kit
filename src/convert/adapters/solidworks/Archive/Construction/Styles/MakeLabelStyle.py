from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeLabelStyle(*, KindValue: str, FontName: str) -> dict[str, object]:
    if KindValue not in (
        "detail",
        "section",
        "auxiliary",
        "orthographic",
        "miscellaneous",
    ):
        raise ValueError(f"unsupported label style {KindValue!r}")
    FieldsValue: dict[str, object] = {
        "f8": 2,
        "fc": 1,
        "f10": 0,
        "f14": 1,
        "f18": 1,
        "f1c": 1,
        "f20": 0,
        "f24": 0,
        "f28": 0,
        "f2c": 0,
        "f38": 0,
        "f44": 1,
        "f48": -1,
        "f58": 0,
        "f5c": 4,
        "f88": "",
        "f90": "",
        "f30": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f3c": MakeLineWidth(CategoryValue=0, WidthValue=-1),
    }
    for OffsetValue in (152, 160, 168, 176, 184, 192):
        FieldsValue[f"f{OffsetValue:x}"] = MakeCharFormat(
            FontName=FontName, HeightValue=0.0035, PointHeight=0
        )
    if KindValue == "detail":
        FieldsValue.update({"fc8": 0, "fcc": 24})
    elif KindValue == "section":
        FieldsValue.update(
            {
                "fc": 2,
                "f10": 0,
                "f2c": 3,
                "f30": MakeLineWidth(CategoryValue=2, WidthValue=-1),
                "fc8": 0.00635,
                "fd0": 0.002032,
                "fd8": 0.0127,
                "fe0": 0,
                "fe4": 2,
                "fe8": 1,
                "fec": 1,
                "ff0": 1,
            }
        )
    elif KindValue == "auxiliary":
        FieldsValue.update({"f8": 1, "fc": 1, "f10": 1, "f58": 0, "fc8": 1})
    else:
        FieldsValue.update({"f8": 0, "fc": 0, "fc8": 0, "fcc": 0})
    return FieldsValue
