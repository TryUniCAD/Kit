from collections.abc import Sequence
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakePrintWidths(*, WidthsValue: Sequence[float]) -> dict[str, object]:
    if (
        not isinstance(CastValue(object, WidthsValue), Sequence)
        or isinstance(CastValue(object, WidthsValue), (str, bytes, bytearray))
        or len(WidthsValue) != 8
    ):
        raise ValueError("the eight authored print line widths are required")
    return {
        f"f{8 + 4 * IndexValue:x}": ReadStyleNum(
            ValueInput, "print line width", LowerLimit=0
        )
        for (IndexValue, ValueInput) in enumerate(WidthsValue)
    }
