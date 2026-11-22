from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoStyle import (
    MakeAnnoStyle,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeAnnoDefs(*, FontName: str, LanguageId: int) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": 0.00625,
        "f10": 1,
        "f14": 0,
        "f18": 0,
        "f1c": 1,
        "f20": 3,
        "f24": 1,
        "f28": 0,
        "f2c": 1,
        "f30": 1,
        "f34": 1,
        "f38": 0,
    }
    for FieldName, KindValue in (
        ("f40", "cloud"),
        ("fa0", "weld"),
        ("f108", "surface_finish"),
        ("f178", "bend"),
        ("f1e8", "gtol"),
        ("f250", "datum"),
        ("f2c0", "balloon"),
        ("f398", "view_location"),
        ("f418", "note"),
        ("f4a0", "base"),
    ):
        FieldsValue[FieldName] = MakeAnnoStyle(
            KindValue=KindValue, FontName=FontName, LanguageId=LanguageId
        )
    return FieldsValue
