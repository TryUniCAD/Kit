from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Definition.Construction.ReadSavePartValue import (
    ReadSavePref,
)
from convert.adapters.solidworks.Archive.Definition.Construction.SavePartSlots import (
    KSavePartSlots,
)


# all native assembly save preferences must be supplied by the caller before serializing
def MakeSavePrefs(
    PreferenceValues: Mapping[str, bool | int | float],
) -> dict[str, object]:
    if PreferenceValues.keys() != KSavePartSlots.keys():
        raise ValueError(
            "SOLIDWORKS save-as-part preferences require every slot from 5fc through 605"
        )
    return {
        "f08": 0,
        **{
            FieldName: ReadSavePref(SlotName, PreferenceValues[SlotName])
            for SlotName, FieldName in KSavePartSlots.items()
        },
    }
