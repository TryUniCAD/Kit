from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)


# source owned ui preferences must remain explicit inputs while separate unsupported document and model presentation owners stay outside this boundary
@DataClass(frozen=True, slots=True)
class RevSourceUi:
    SettingsValue: ModelDefSettings
    DensityValue: float
