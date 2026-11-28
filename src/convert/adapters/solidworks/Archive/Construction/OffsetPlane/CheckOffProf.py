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


# dimension owners require exact identity of the generated local offset reference
def CheckOffProf(GraphValue: ProfileGraph, OffsetValue: OffsetGraph) -> None:
    Profile = GraphValue.ProfileValue
    OwnerValue = ArchiveNode.RequireNode(Profile.FieldsValue.get("owner"))
    Reference = MakeOffsetSup(OwnerValue, OffsetValue)
    Actual = ArchiveNode.RequireNode(Profile.FieldsValue.get("pd_f78"))
    ActualComp = ArchiveNode.RequireNode(Actual.FieldsValue.get("f58"))
    if (
        GraphValue.FrameValue != OffsetValue.FrameValue
        or Actual is not GraphValue.ReferenceValue
        or Actual.ClassValue != Reference.ClassValue
        or ActualComp.FieldsValue != {"has_ext": 0, "owner": OwnerValue}
        or {
            NameValue: Value
            for NameValue, Value in Actual.FieldsValue.items()
            if NameValue != "f58"
        }
        != {
            NameValue: Value
            for NameValue, Value in Reference.FieldsValue.items()
            if NameValue != "f58"
        }
    ):
        raise ValueError("offset profile requires its actual linked datum frame")
