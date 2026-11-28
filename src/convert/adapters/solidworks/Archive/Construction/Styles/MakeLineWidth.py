from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeLineWidth(*, CategoryValue: int, WidthValue: float) -> dict[str, object]:
    if type(CastValue(object, CategoryValue)) is not int or not 0 <= CategoryValue <= 7:
        raise ValueError("line-weight category must be a native category in 0..7")
    WidthValue = ReadStyleNum(WidthValue, "line width")
    if WidthValue < 0 and WidthValue != -1:
        raise ValueError(
            "line width must be nonnegative or the native -1 category-width sentinel"
        )
    return {"f06": CategoryValue, "f00": WidthValue}
