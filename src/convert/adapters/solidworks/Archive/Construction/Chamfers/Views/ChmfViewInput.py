from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckViewArgs import (
    CheckViewArgs,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# explicitly placed chamfer labels retain separate station clearance and witness intent
@DataClass(frozen=True, slots=True)
class ChmfViewInput:
    CatalogValue: tuple[AnnoViewInput, ...]
    DriverView: str
    DistanceText: tuple[float, float]
    AngleText: tuple[float, float]
    WitnessLength: float
    DesignIntent: bool
    LeadersValue: tuple[int, int]

    # invalid placement is refused before it can reach any display allocation
    def __post_init__(self) -> None:
        Station, Clearance = tuple(RequireScalar(Value) for Value in self.DistanceText)
        TextX, TextY = self.AngleText
        _ = RequireScalar(TextX), RequireScalar(TextY)
        if (
            Station <= 1.0
            or Clearance == 0.0
            or RequireScalar(self.WitnessLength) <= 0.0
        ):
            raise ValueError("chamfer display requires finite exterior label placement")
        LengthLeader, AngleLeader = self.LeadersValue
        CheckViewArgs(self.DesignIntent, LengthLeader)
        CheckViewArgs(self.DesignIntent, AngleLeader)
