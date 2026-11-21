from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeLineFont(*, NameValue: str) -> dict[str, object]:
    return {
        "f08": ReadStyleText(NameValue, "line-style name"),
        "f10": MakeLineWidth(CategoryValue=0, WidthValue=-1),
        "f18": 0,
    }
