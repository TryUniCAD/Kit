from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import (
    MakePlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.RotateVector import (
    RotateVector,
)


# resolved endpoint geometry is derived by applying the actual occurrence placement to the child datum basis
def PlaceDatum(Frame: PlaneFrame, Placement: Mapping[str, object]) -> PlaneFrame:
    Matrix, Translation = ReadRigidXform(Placement)
    RootValue = RotateVector(Matrix, Frame.OriginValue)
    Origin = tuple(
        First + Second for First, Second in zip(Translation, RootValue, strict=True)
    )
    return MakePlaneFrame(
        (Origin[0], Origin[1], Origin[2]),
        RotateVector(Matrix, Frame.AxisU),
        RotateVector(Matrix, Frame.AxisV),
    )
