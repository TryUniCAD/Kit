from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetSup import (
    MakeOffsetSup,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# a translated radial view is valid only through the actual offset datum and its local centre
def CheckOffRadial(
    GraphValue: ProfileGraph, OffsetValue: OffsetGraph, IsDiameter: bool
) -> None:
    Profile = GraphValue.ProfileValue
    OwnerValue = ArchiveNode.RequireNode(Profile.FieldsValue.get("owner"))
    Reference = MakeOffsetSup(OwnerValue, OffsetValue)
    Actual = ArchiveNode.RequireNode(Profile.FieldsValue.get("pd_f78"))
    ActualComp = ArchiveNode.RequireNode(Actual.FieldsValue.get("f58"))
    Values = Actual.FieldsValue
    Point = RequireRecord(NeedCircle(GraphValue).CenterValue.FieldsValue.get("pos"))
    if (
        IsDiameter
        or GraphValue.FrameValue != OffsetValue.FrameValue
        or Actual is not GraphValue.ReferenceValue
        or Actual.ClassValue != Reference.ClassValue
        or ActualComp.FieldsValue != {"has_ext": 0, "owner": OwnerValue}
        or {
            NameValue: Value
            for NameValue, Value in Values.items()
            if NameValue != "f58"
        }
        != {
            NameValue: Value
            for NameValue, Value in Reference.FieldsValue.items()
            if NameValue != "f58"
        }
        or tuple(Point[NameValue] for NameValue in ("x", "y")) != (0.0, 0.0)
    ):
        raise ValueError("radial view requires the actual centred offset sketch")
