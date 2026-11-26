from convert.adapters.solidworks.Archive.Construction.Styles.MakeFinishData import (
    MakeFinishData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeHelperFont import (
    MakeHelperFont,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeWeldData(*, FontName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": 0,
        "f90": "",
        "fa8": "",
        "fd8": 0,
        "fdc": 0,
        "fe8": 1,
        "ff0": MakeHelperFont(FontName=FontName),
        "f150": 1,
        "f154": 1,
        "f158": MakeHelperFont(FontName=FontName),
        "f1b8": MakeHelperFont(FontName=FontName),
        "f260": MakeFinishData(FontName=FontName),
        "f268": MakeFinishData(FontName=FontName),
    }
    FieldsValue.update(
        {
            f"f{16 + 8 * SideValue + 16 * IndexValue:x}": ""
            for SideValue in range(2)
            for IndexValue in range(8)
        }
    )
    FieldsValue.update({f"f{536 + 8 * IndexValue:x}": "" for IndexValue in range(5)})
    FieldsValue.update(
        {
            f"f{OffsetValue:x}": 0
            for OffsetValue in (
                152,
                156,
                160,
                164,
                176,
                180,
                184,
                188,
                192,
                196,
                200,
                204,
                208,
                212,
                224,
                228,
                576,
                580,
                584,
                588,
                592,
                596,
                600,
            )
        }
    )
    return FieldsValue
