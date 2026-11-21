from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.EndpointData import (
    EndpointData,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the supported no flip distance branch requires equal oriented plane normals and positive ordered world separation
def CheckDistPlanes(Endpoints: tuple[EndpointData, EndpointData]) -> float:
    First, Second = (Value.FrameValue for Value in Endpoints)
    if not IsClose(
        DotVector(First.NormalValue, Second.NormalValue),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError("distance principal planes must have the same orientation")
    Difference = tuple(
        Other - Current
        for Current, Other in zip(First.OriginValue, Second.OriginValue, strict=True)
    )
    Separation = RequireScalar(
        DotVector((Difference[0], Difference[1], Difference[2]), First.NormalValue)
    )
    if Separation <= 0:
        raise ValueError("distance principal planes require positive signed separation")
    return Separation
