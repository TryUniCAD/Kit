from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeTableStyle import (
    MakeTableStyle,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeTableDefs(*, FontName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": 1,
        "f328": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
        "f330": 0.0005,
        "f338": 0.001,
    }
    for FieldName, KindValue in (
        ("f10", "general"),
        ("f50", "revision"),
        ("fb0", "bom"),
        ("f110", "title_block"),
        ("f150", "hole"),
        ("f1d0", "weld"),
        ("f218", "bend"),
        ("f268", "punch"),
        ("f2e0", "family"),
    ):
        FieldsValue[FieldName] = MakeTableStyle(KindValue=KindValue, FontName=FontName)
    return FieldsValue
