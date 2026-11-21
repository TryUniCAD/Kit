from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileList import (
    NeedProfileList,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileRows import (
    NeedProfileRows,
)


# populated sets and linked annotation state remain outside understood profile display retention
def CanHideProfile(FieldsValue: Mapping[str, object]) -> bool:
    KeysValue = NeedProfileRows(FieldsValue.get("f1e0"))
    CountValue = FieldsValue.get("n1e0", len(KeysValue))
    FlagsValue = FieldsValue.get("f200")
    LinkedValue = FieldsValue.get("linked")
    if (
        KeysValue
        or type(CountValue) is not int
        or CountValue != 0
        or type(FlagsValue) is not int
        or FlagsValue not in (0, 1)
        or type(LinkedValue) is not int
        or LinkedValue != 0
        or "ff8" not in FieldsValue
        or FieldsValue["ff8"] is not None
        or NeedProfileList(FieldsValue.get("f68"))
        or NeedProfileList(FieldsValue.get("fb0"))
    ):
        raise BodyUnsupported(
            "drawing profile display has unqualified auxiliary or flag state"
        )
    return bool(FlagsValue & 1)
