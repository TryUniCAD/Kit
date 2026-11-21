from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import (
    FontBinding,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.LinePattern import (
    LinePattern,
)


# typed collections must preserve distinct category values and explicit ordered pattern definitions
def CheckLineInput(
    PatternValues: tuple[LinePattern, ...], BindingValues: tuple[FontBinding, ...]
) -> None:
    if (
        type(CastValue(object, PatternValues)) is not tuple
        or len(PatternValues) >= 1 << 31
        or any(type(Value) is not LinePattern for Value in PatternValues)
        or type(CastValue(object, BindingValues)) is not tuple
        or len(BindingValues) > 0xFFFF
        or any(type(Value) is not FontBinding for Value in BindingValues)
    ):
        raise TypeError("line tables require typed immutable bounded collections")
    PatternNames = tuple(Value.NameValue.casefold() for Value in PatternValues)
    CategoryNames = tuple(Value.CategoryValue for Value in BindingValues)
    if len(set(PatternNames)) != len(PatternNames) or len(set(CategoryNames)) != len(
        CategoryNames
    ):
        raise ValueError("line tables require distinct pattern and category identities")
