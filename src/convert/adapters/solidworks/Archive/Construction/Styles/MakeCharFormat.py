from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeCharFormat(
    *,
    FontName: str,
    HeightValue: float,
    PointHeight: int,
    WeightValue: int = 400,
    LineSpacing: float = 0.0,
) -> dict[str, object]:
    FontName = ReadStyleText(FontName, "font name")
    if not FontName:
        raise ValueError(
            "an explicit authored font is required; the localized font resource is not a default input"
        )
    if (
        type(CastValue(object, PointHeight)) is not int
        or not 0 <= PointHeight <= 2147483647
    ):
        raise ValueError("point height must be a nonnegative authored integer")
    if type(CastValue(object, WeightValue)) is not int or not 1 <= WeightValue <= 1000:
        raise ValueError("font weight must be an authored integer in 1..1000")
    HeightValue = ReadStyleNum(HeightValue, "character height")
    if HeightValue <= 0 and HeightValue != -1 or (HeightValue > 0 and PointHeight):
        raise ValueError(
            "character height must be positive with point height zero, or use the native -1 point-height mode"
        )
    return {
        "f08": FontName,
        "f10": HeightValue,
        "f18": PointHeight,
        "f20": 0.0,
        "f28": ReadStyleNum(LineSpacing, "line spacing", LowerLimit=0),
        "f30": 0,
        "f38": 1.0,
        "f40": 0.0,
        "f48": 0.0,
        "f50": 1.0,
        "f58": WeightValue,
    }
