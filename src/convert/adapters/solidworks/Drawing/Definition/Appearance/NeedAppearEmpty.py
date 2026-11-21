from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# populated or inconsistent appearance references need projection before they can be admitted
def NeedAppearEmpty(FieldsValue: Mapping[str, object]) -> None:
    CountValue = FieldsValue.get("n")
    RowsValue = FieldsValue.get("items")
    if (
        type(CountValue) is not int
        or CountValue != 0
        or not isinstance(RowsValue, (tuple, list))
        or len(CastValue(Sequence[object], RowsValue)) != 0
    ):
        raise BodyUnsupported(
            "drawing appearance state requires exactly empty reference rows"
        )
