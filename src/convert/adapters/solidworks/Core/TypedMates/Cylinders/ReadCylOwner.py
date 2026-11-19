from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the selected lateral surface must retain the actual extrusion profile arc and manager atom
def ReadCylOwner(LinkValue: NativeLink, AtomValue: int) -> tuple[ArchiveNode, int]:
    ModelValue = RequireNode(LinkValue.ConfigValue.RootValue, "moPart_c")
    FeaturesValue = tuple(
        Value
        for Value in LinkValue.ResolvedValue.RootsValue
        if Value is not None and Value.ClassValue.NameValue == "moExtrusion_c"
    )
    if len(FeaturesValue) != 1:
        raise ValueError("concentric child has no unique actual extrusion")
    FeatureValue = FeaturesValue[0]
    NativeAtom = ReadOutputAtom(FeatureValue)
    ManagerValue = RequireRecord(ModelValue.FieldsValue.get("fd88"))
    AtomRows = ReadRows(ManagerValue.get("atoms"))
    FeatureId = FieldInt(FeatureValue.FieldsValue, "f08")
    if (
        len(AtomRows) != 1
        or FieldInt(ManagerValue, "n6c") != 1
        or AtomRows[0].get("o") is not NativeAtom
        or FieldInt(NativeAtom.FieldsValue, "f140") != AtomValue
        or any(
            FieldInt(NativeAtom.FieldsValue, NameValue) != FeatureId
            for NameValue in ("f12c", "f130")
        )
    ):
        raise ValueError("concentric child kernel and actual archive atom differ")
    ProfileList = RequireRecord(
        RequireRecord(FeatureValue.FieldsValue.get("f60")).get("list")
    )
    Profiles = ReadRows(ProfileList.get("items"))
    if len(Profiles) != 1:
        raise ValueError("concentric child requires one actual profile")
    Profile = RequireNode(Profiles[0].get("o"), "moProfileFeature_c")
    SketchValue = RequireNode(Profile.FieldsValue.get("pd_f80"), "sgSketch").FieldsValue
    ArcsValue = ReadRows(SketchValue.get("arcs"))
    if len(ArcsValue) != 1:
        raise ValueError("concentric child requires one actual circle arc")
    return FeatureValue, FieldInt(RequireRecord(ArcsValue[0].get("arc")), "f08")
