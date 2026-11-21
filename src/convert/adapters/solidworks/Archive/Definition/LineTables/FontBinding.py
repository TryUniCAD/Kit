from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# each native category owns its own font copy with explicit preset weight and end cap inputs
@DataClass(frozen=True, slots=True)
class FontBinding:
    CategoryValue: str
    FontName: str
    WeightValue: int
    EndCapValue: int

    # starred categories are filtered by native store and unqualified width or cap modes must remain refused
    def __post_init__(self) -> None:
        if (
            not ReadStyleText(self.CategoryValue, "line font category")
            or "*" in self.CategoryValue
            or not ReadStyleText(self.FontName, "line font name")
        ):
            raise ValueError(
                "line font category and name must be persistent nonempty text"
            )
        if type(
            CastValue(object, self.WeightValue)
        ) is not int or self.WeightValue not in (0, 1, 2):
            raise ValueError("line font preset weight is outside the proven profile")
        if type(
            CastValue(object, self.EndCapValue)
        ) is not int or self.EndCapValue not in (0, 2):
            raise ValueError("line font end cap is outside the proven profile")
