from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import (
    AppearanceState,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.ReadAppearCount import (
    ReadAppearCount,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.NeedAppearMap import (
    NeedAppearMap,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.NeedAppearEmpty import (
    NeedAppearEmpty,
)


# current drawings may retain an empty manager without losing their actual allocation state
def ReadAppearState(Document: ArchiveNode, VersionValue: int) -> AppearanceState:
    ClassValue = Document.ClassValue
    if (
        VersionValue != 19000
        or not isinstance(ClassValue, RuntimeClass)
        or ClassValue != RuntimeClass("uiDrawingDoc_c", 1)
    ):
        raise BodyUnsupported("drawing appearance state requires current ui ownership")
    FieldsValue = Document.FieldsValue
    PresenceValue = FieldsValue.get("has_pwmaterial")
    if type(PresenceValue) is not int or PresenceValue not in (0, 1):
        raise BodyUnsupported("drawing appearance presence is outside the profile")
    if PresenceValue == 0:
        return AppearanceState(False, 1)
    ManagerValue = NeedAppearMap(FieldsValue.get("f1110"))
    References = NeedAppearMap(ManagerValue.get("list"))
    NeedAppearEmpty(References)
    return AppearanceState(True, ReadAppearCount(ManagerValue))
