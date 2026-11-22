from convert.adapters.solidworks.Archive.Construction.Styles.MakeTextArray import (
    MakeTextArray,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeGtolFrame() -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": "",
        "f10": None,
        "f18": None,
        "f20": 0,
        "f24": 0,
        "f28": 0,
        "f30": "",
        "f38": "",
        "f40": 0,
        "f48": "",
        "f50": "",
        "f148": 0,
        "n2b8": 0,
        "f2b8": [],
    }
    FieldsValue.update(
        {
            f"f{OffsetValue:x}": MakeTextArray(ValuesInput=())
            for OffsetValue in (88, 128, 168, 208, 248, 288)
        }
    )
    return FieldsValue
