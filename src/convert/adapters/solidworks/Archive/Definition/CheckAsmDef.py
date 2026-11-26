from collections.abc import Mapping

from convert.adapters.base.ContractCompat import IsObjectDict
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Definition.Construction.SavePartSlots import (
    KSavePartSlots,
)


# the ordinary assembly stores normalized preferences and a bounded fraction in its own tail
def CheckAsmDef(FieldsValue: Mapping[str, object]) -> None:
    PrefValue = FieldsValue.get("f1b48")
    if not IsObjectDict(PrefValue):
        raise BodyUnsupported(
            "SOLIDWORKS assembly Definition requires inline preferences"
        )
    BoolValues = (
        FieldsValue.get("f1a48"),
        *(
            PrefValue.get(FieldName)
            for SlotName, FieldName in KSavePartSlots.items()
            if SlotName not in ("5fd", "5ff", "605")
        ),
    )
    if any(type(Value) is not int or Value not in (0, 1) for Value in BoolValues):
        raise BodyUnsupported("SOLIDWORKS assembly Definition has an alternate boolean")
    Fraction = ReadStyleNum(
        PrefValue.get("f10"), "SOLIDWORKS save-as-part fraction", 0.0
    )
    if Fraction > 0.9:
        raise BodyUnsupported(
            "SOLIDWORKS save-as-part fraction exceeds the native range"
        )
    _ = ReadStyleNum(PrefValue.get("f20"), "SOLIDWORKS save-as-part preference 5ff")
    _ = ReadStyleNum(
        FieldsValue.get("f19b8"), "SOLIDWORKS assembly Definition field f19b8"
    )
