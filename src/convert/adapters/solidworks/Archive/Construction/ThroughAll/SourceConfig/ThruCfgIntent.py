from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import (
    ManagerInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)
from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNumber,
)


# source configuration identity and document preferences need semantic inputs instead of saved field bags
@DataClass(frozen=True, slots=True)
class ThruCfgIntent:
    ModelName: str
    ManagerValue: ManagerInput
    DefinitionValue: ModelDefSettings
    DensityValue: float

    # single configuration checks preserve the measured source scope without enabling incomplete part conversion
    def __post_init__(self) -> None:
        if not ReadStyleText(self.ModelName, "source model name"):
            raise ValueError("source model identity must have an actual name")
        if (
            type(self.ManagerValue) is not ManagerInput
            or len(self.ManagerValue.ConfigValues) != 1
            or self.ManagerValue.CurrentIndex != 0
        ):
            raise ValueError(
                "through-all source intent requires one actual selected configuration"
            )
        if (
            type(self.DefinitionValue) is not ModelDefSettings
            or self.DefinitionValue.VersionValue != 19000
        ):
            raise ValueError(
                "through-all source intent requires typed version 19000 document settings"
            )
        if RequireDefNumber(self.DensityValue) <= 0:
            raise ValueError("through-all source document density must be positive")
