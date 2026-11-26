from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# local geometry must retain an allocated ordinary profile and its actual caller owned plane reference
def RequireProfile(ProfileValue: ArchiveNode) -> None:
    ProfileValue = ArchiveNode.RequireNode(ProfileValue)
    ClassValue = ProfileValue.ClassValue
    if type(ClassValue) is not RuntimeClass or (
        ClassValue.NameValue,
        ClassValue.SchemaValue,
    ) != ("moProfileFeature_c", 1):
        raise ValueError(
            "polygon owner must be a concrete ordinary profile with schema one"
        )
    FeatureId = ProfileValue.FieldsValue.get("f08")
    if type(FeatureId) is not int or not 0 <= FeatureId <= 0x7FFFFFFF:
        raise ValueError("polygon profile must have an allocated feature identifier")
    if (
        ProfileValue.FieldsValue["f3dc"] != 0
        or ProfileValue.FieldsValue["pd_f110"] is not None
    ):
        raise ValueError(
            "polygon construction requires an ordinary unshared local profile"
        )
    PlaneValue = ArchiveNode.RequireNode(ProfileValue.FieldsValue["pd_f78"])
    PlaneClass = PlaneValue.ClassValue
    if type(PlaneClass) is not RuntimeClass or (
        PlaneClass.NameValue,
        PlaneClass.SchemaValue,
    ) != ("moCompRefPlane_c", 1):
        raise ValueError(
            "polygon profile requires its actual component plane reference"
        )
    if "pd_ff0" not in ProfileValue.FieldsValue:
        raise ValueError("polygon profile requires an explicit caller owned frame")
