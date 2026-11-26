from collections.abc import Sequence
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeTextArray(*, ValuesInput: Sequence[str]) -> dict[str, object]:
    if not isinstance(CastValue(object, ValuesInput), Sequence) or isinstance(
        CastValue(object, ValuesInput), (str, bytes, bytearray)
    ):
        raise ValueError("authored names must be a sequence")
    return {
        "n": len(ValuesInput),
        "items": [
            {"s": ReadStyleText(ValueInput, "authored name")}
            for ValueInput in ValuesInput
        ],
    }
