from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoData import (
    MakeAnnoData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeHelperFont import (
    MakeHelperFont,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeFinishData(*, FontName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f08": 0,
        "f78": 0,
        "f7c": 0,
        "f80": 0.78539816339745,
        "f98": 0,
        "f9c": 0,
        "fb0": 0.0,
        "fb8": 1,
        "fc0": MakeHelperFont(FontName=FontName),
        "f128": MakeAnnoData(FontName=FontName),
    }
    FieldsValue.update(
        {
            f"f{OffsetValue:x}": ""
            for OffsetValue in (16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 136, 144)
        }
    )
    FieldsValue.update(
        {
            f"f{OffsetValue:x}": 0
            for OffsetValue in (104, 108, 112, 116, 160, 164, 168, 172, 288, 292)
        }
    )
    return FieldsValue
