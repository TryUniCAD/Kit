from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import (
    AppearanceState,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.NeedAppearEmpty import (
    NeedAppearEmpty,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.NeedAppearMap import (
    NeedAppearMap,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.ReadAppearCount import (
    ReadAppearCount,
)


# shared empty appearance semantics preserve the actual allocator without promoting populated reference maps
def ReadEmptyAppr(FieldsValue: Mapping[str, object]) -> AppearanceState:
    PresenceValue = FieldsValue.get("has_pwmaterial")
    if type(PresenceValue) is not int or PresenceValue not in (0, 1):
        raise BodyUnsupported("part appearance presence is outside the empty profile")
    if PresenceValue == 0:
        if "f1110" in FieldsValue:
            raise BodyUnsupported(
                "absent appearance state has an unexplained manager body"
            )
        return AppearanceState(False, 1)
    ManagerValue = NeedAppearMap(FieldsValue.get("f1110"))
    if set(ManagerValue) != {"f08", "f0c", "list"}:
        raise BodyUnsupported("appearance manager has absent or unrepresented fields")
    References = NeedAppearMap(ManagerValue["list"])
    if set(References) != {"n", "items"}:
        raise BodyUnsupported("appearance reference list has unrepresented fields")
    NeedAppearEmpty(References)
    return AppearanceState(True, ReadAppearCount(ManagerValue))
