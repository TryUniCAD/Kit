from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.geometry.Models.Transform import Transform


# the signed stock and its public drivers must use the same profile and datum proof
@DataClass(frozen=True, slots=True)
class AxisStock:
    OwnerValue: ExtrudeOwner
    LoopValue: LineLoop
    FrameValue: Transform
    PlaneId: int
