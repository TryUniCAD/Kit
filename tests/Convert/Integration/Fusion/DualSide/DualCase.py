from dataclasses import dataclass as MakeDataClass
from pathlib import Path

from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform


# committed source observations bind independent side controls to their actual archive
@MakeDataClass(frozen=True, slots=True)
class DualCase:
    Source: Path
    Digest: str
    Identity: str
    Profile: CircleGeometry
    Frame: Transform
    FirstMm: float
    SecondMm: float
    FirstTaper: float
    SecondTaper: float
    Reading: dict[str, object]
