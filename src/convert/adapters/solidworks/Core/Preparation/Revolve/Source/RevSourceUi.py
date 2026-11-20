from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)


# source owned ui preferences must remain explicit inputs while separate unsupported document and model presentation owners stay outside this boundary
@DataClass(frozen=True, slots=True)
class RevSourceUi:
    SettingsValue: ModelDefInput
    DensityValue: float
