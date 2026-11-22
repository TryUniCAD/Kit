from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.CircularPartition import (
    CheckRoundBody,
    CylinderData,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# both read modes compare the same physical cylinder against its live sketch and boss
def CheckSavedRound(BodyValue: BrepModel, NativeValue: NativeModel) -> CylinderData:
    (SketchValue,) = NativeValue.sketches
    (Operation,) = NativeValue.operations
    CircleValue = SketchValue.TypedCircle
    FrameValue = SketchValue.TypedFrame
    Length = Operation.length_mm
    if (
        CircleValue is None
        or FrameValue is None
        or Length is None
        or FrameValue.z_axis != SpaceVector(0.0, 0.0, 1.0)
        or Operation.direction_code != 0
    ):
        raise ValueError("saved circle geometry lacks its live sketch and boss proof")
    StartX, StartY = CircleValue.CenterValue
    AxisValue = FrameValue.z_axis
    return CheckRoundBody(
        BodyValue,
        (StartX / 1000, StartY / 1000, 0.0),
        (AxisValue.x, AxisValue.y, AxisValue.z),
        Length / 1000,
        CircleValue.RadiusValue / 1000,
    )
