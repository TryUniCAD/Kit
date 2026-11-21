from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)


# manager and configuration feature moments remain independent from revision and save clocks
@DataClass(frozen=True, slots=True)
class ConfigEvent:
    MomentValue: FeatureInstant
    CreatedBy: FeatureTarget

    # this source component retains only the independently mapped modern ordinary provenance profile
    def __post_init__(self) -> None:
        if type(self.MomentValue) is not FeatureInstant:
            raise ValueError(
                "configuration event requires a precise typed feature moment"
            )
        if (
            type(self.CreatedBy) is not FeatureTarget
            or self.CreatedBy.FileVersion != 19000
            or self.CreatedBy.ServicePack != 5
            or self.CreatedBy.SubservicePack not in (0, 2)
        ):
            raise ValueError(
                "configuration event requires qualified creation provenance"
            )
