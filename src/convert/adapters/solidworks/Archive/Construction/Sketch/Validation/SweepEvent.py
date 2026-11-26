from dataclasses import dataclass as DataClass, field as DataField

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)


# event groups preserve coincident starts ends and vertical ranges at one abscissa
@DataClass(slots=True)
class SweepEvent:
    StartsValue: list[SweepEdge] = DataField(default_factory=list[SweepEdge])
    EndsValue: list[SweepEdge] = DataField(default_factory=list[SweepEdge])
    VerticalValue: list[SweepEdge] = DataField(default_factory=list[SweepEdge])
