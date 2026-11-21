from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdDatum import (
    ReadColdDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

# the initial archive profile has measured front and right signed bases in feature order
KColdFrames = (
    Transform(
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
    ),
    Transform(
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
    ),
)


# the depthless profile must share the actual datum of the coherently selected stock
def ReadColdFrames(
    LinkValue: NativeLink,
    OwnersValue: tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner],
    Features: Mapping[int, ArchiveNode],
    Selected: int,
) -> tuple[Transform, Transform, Transform]:
    FirstValue, SecondValue, CutValue = (
        ReadColdDatum(LinkValue, OwnerValue.ProfileValue, Features)
        for OwnerValue in OwnersValue
    )
    ExpectedFrame, ExpectedDatum = (FirstValue, SecondValue)[Selected]
    if (
        (FirstValue[0], SecondValue[0]) != KColdFrames
        or CutValue[0] != ExpectedFrame
        or CutValue[1] is not ExpectedDatum
    ):
        raise ValueError("cut and selected stock do not share their exact signed datum")
    return FirstValue[0], SecondValue[0], CutValue[0]
