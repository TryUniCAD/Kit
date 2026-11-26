from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# deterministic slope and identity ties preserve ordered edges at coincident event coordinates
def SweepEdgeKey(
    StateValue: SweepState, EdgeValue: SweepEdge
) -> tuple[Fraction, Fraction, int]:
    if EdgeValue.SlopeValue is None:
        raise ValueError("vertical polygon edge cannot enter the active ordered tree")
    return (
        EdgeValue.GetOrdinate(StateValue.PositionX),
        EdgeValue.SlopeValue,
        EdgeValue.IndexValue,
    )
