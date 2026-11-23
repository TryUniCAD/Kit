from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.CheckOffProf import (
    CheckOffProf,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# a translated radial view is valid only through the actual offset datum and its local centre
def CheckOffRadial(
    GraphValue: ProfileGraph, OffsetValue: OffsetGraph, IsDiameter: bool
) -> None:
    CheckOffProf(GraphValue, OffsetValue)
    Point = RequireRecord(NeedCircle(GraphValue).CenterValue.FieldsValue.get("pos"))
    if IsDiameter or tuple(Point[NameValue] for NameValue in ("x", "y")) != (0.0, 0.0):
        raise ValueError("radial view requires the actual centred offset sketch")
