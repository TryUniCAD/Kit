from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import (
    EmptyMgrInput,
)
from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import (
    AppearanceState,
)


# holder creation and live publication consume distinct identities from the part appearance manager
def PlanLookIds(InputValue: PartLookInput) -> tuple[int, int, EmptyMgrInput]:
    StartValue = InputValue.StartAppearanceId
    if (
        type(CastValue(object, StartValue)) is not int
        or not 1 <= StartValue <= (1 << 64) - 3
    ):
        raise ValueError(
            "part rendering needs two nonwrapping appearance allocation events"
        )
    return (
        StartValue,
        StartValue + 1,
        EmptyMgrInput(InputValue.EmptyBomOnWire, AppearanceState(True, StartValue + 2)),
    )
