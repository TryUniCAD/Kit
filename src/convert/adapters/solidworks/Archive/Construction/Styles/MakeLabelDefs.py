from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLabelStyle import (
    MakeLabelStyle,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeLabelDefs(*, FontName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f8": 1,
        "fc": 1,
        "f458": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
    }
    for FieldName, KindValue in (
        ("f18", "detail"),
        ("fe8", "section"),
        ("f1e8", "auxiliary"),
        ("f2b8", "orthographic"),
        ("f388", "miscellaneous"),
    ):
        FieldsValue[FieldName] = MakeLabelStyle(KindValue=KindValue, FontName=FontName)
    return FieldsValue
