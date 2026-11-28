from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# the separate selectable source point needs a distinct owner even at the document origin
@MakeDataClass(frozen=True, slots=True)
class BoxOriginPoint:
    OriginId: str
    RecordId: str
    ObjectName: str
    LabelValue: str
    PointMm: SpaceVector
    RecordShown: bool


# the actual origin group can include a point in addition to its three line datums
@MakeDataClass(frozen=True, slots=True)
class BoxDatums:
    AxisValue: BoxOriginAxes
    PointValue: BoxOriginPoint | None
