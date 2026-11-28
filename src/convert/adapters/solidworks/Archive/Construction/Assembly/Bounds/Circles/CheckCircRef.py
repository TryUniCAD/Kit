from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
    ReadRows,
)


# child bounds must use the same actual front datum profile and boss parents that the emitted archive owns
def CheckCircRef(ChildValue: PartCandidate) -> None:
    RootValue = ChildValue.SystemValue.RootValue
    Profile = RequireNode(ChildValue.ProfileValue.ProfileValue, "moProfileFeature_c")
    BossValue = RequireNode(ChildValue.BossValue.FeatureValue, "moExtrusion_c")
    Reference = RequireNode(ChildValue.ProfileValue.ReferenceValue, "moCompRefPlane_c")
    PlaneValue = ChildValue.SystemValue.SystemValues.PlaneValues["z"]
    FrameValue = PrincipalFrame("z")
    Parents = ReadRows(
        RequireRecord(RequireRecord(BossValue.FieldsValue["f60"])["list"])["items"]
    )
    Component = RequireNode(Reference.FieldsValue.get("f58"), "moUnitComponent_c")
    if (
        Profile.FieldsValue.get("owner") is not RootValue
        or BossValue.FieldsValue.get("owner") is not RootValue
        or len(Parents) != 1
        or Parents[0].get("o") is not Profile
        or ChildValue.ProfileValue.FrameValue != FrameValue
        or Profile.FieldsValue.get("pd_ff0") != FrameXform(FrameValue)
        or Profile.FieldsValue.get("pd_f78") is not Reference
        or Component.FieldsValue.get("owner") is not RootValue
        or FieldInt(Reference.FieldsValue, "f100") != 3
        or RequireRecord(Reference.FieldsValue.get("ff0")).get("f00")
        != PlaneValue.FieldsValue["f08"]
    ):
        raise ValueError("circle bounds lost actual Front support or feature ownership")
