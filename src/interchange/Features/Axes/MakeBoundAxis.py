from math import fsum as SumExact
from math import isfinite as IsFinite

from interchange.Features.Axes.AxisVector import KAxisTriple
from interchange.Features.CheckAxisFit import CheckAxisFit
from interchange.geometry.Models.VectorSpace import SpaceVector


# rounded model points must remain distinct and incident while signed stations determine orientation
def MakeBoundAxis(
    Origin: KAxisTriple, Direction: KAxisTriple, Stations: tuple[float, float]
) -> tuple[SpaceVector, SpaceVector]:
    SpanValue = Stations[1] - Stations[0]
    if not IsFinite(SpanValue) or SpanValue == 0.0:
        raise ValueError("plane axis requires distinct endpoints with a finite span")
    StartValue, EndValue = (
        SpaceVector(
            *(
                SumExact((Coordinate, Offset * Station))
                for Coordinate, Offset in zip(Origin, Direction)
            )
        )
        for Station in Stations
    )
    CheckAxisFit(StartValue, EndValue, Origin, Direction, CompareDirection=False)
    return StartValue, EndValue
