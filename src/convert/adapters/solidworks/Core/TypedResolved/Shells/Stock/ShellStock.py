from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.geometry.Models.BoundingBox import BoundingBox


# the earlier stock binds an actual rectangular contour and its support datum
@DataClass(frozen=True, slots=True)
class ShellStock:
    OwnerValue: ExtrudeOwner
    LoopValue: LineLoop
    BoundsValue: BoundingBox
    PlaneId: int
