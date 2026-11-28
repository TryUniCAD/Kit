from collections.abc import Sequence

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileMap import (
    NeedProfileMap,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileRows import (
    NeedProfileRows,
)


# explicit native counts must agree with the actual retained list members
def NeedProfileList(Value: object) -> Sequence[object]:
    FieldsValue = NeedProfileMap(Value)
    if set(FieldsValue) - {"n", "items"}:
        raise BodyUnsupported("drawing profile display has unknown native list fields")
    RowsValue = NeedProfileRows(FieldsValue.get("items"))
    CountValue = FieldsValue.get("n", len(RowsValue))
    if (
        type(CountValue) is not int
        or CountValue != len(RowsValue)
        or not 0 <= CountValue < (1 << 31)
    ):
        raise BodyUnsupported("drawing profile display list count disagrees with rows")
    return RowsValue
