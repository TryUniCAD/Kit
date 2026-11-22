from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.CheckSweepInput import (
    CheckSweepInput,
)
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry


# a standard sweep retains both independent exact planar curves and authored physical density
@DataClass(frozen=True, slots=True)
class SweepIntent:
    NameValue: str
    SectionValue: CircleGeometry
    PathValue: ArcGeometry
    DensityValue: float
    OutputValue: SelfFileInput

    # the cold writer admits the measured right section and front quarter arc only
    def __post_init__(self) -> None:
        CheckSweepInput(
            self.NameValue,
            self.SectionValue,
            self.PathValue,
            self.DensityValue,
            self.OutputValue,
        )
