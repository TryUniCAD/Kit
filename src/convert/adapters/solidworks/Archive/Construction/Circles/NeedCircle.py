from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)


# circle operations must retain the actual owned circular sketch before creating dimension references
def NeedCircle(GraphValue: ProfileGraph) -> CircleGraph:
    GeometryValue = GraphValue.GeometryValue
    if type(GeometryValue) is not CircleGraph:
        raise ValueError(
            "radial operation requires a generated ordinary circle profile"
        )
    return GeometryValue
