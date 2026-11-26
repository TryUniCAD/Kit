from dataclasses import dataclass as DataClass, field as DataField
from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNode import (
    SweepNode,
)


# one validation owns its active tree and exact abscissa without shared cached state
@DataClass(slots=True)
class SweepState:
    RootValue: SweepNode | None = None
    NodesValue: dict[int, SweepNode] = DataField(default_factory=dict[int, SweepNode])
    PositionX: Fraction = Fraction(0)
