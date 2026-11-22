from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

# only recovered keyword type vocabulary may identify a default presentation member for timeline normalization
KMemberKinds = {
    "moNotesAreaFtrFolder_c": "Notes",
    "moAmbientLight_c": "Ambient",
    "moDirectionLight_c": "Directional",
}


# custom keyword meaning must remain in its existing feature row even when its identifier matches a default owned member
def CheckMember(Feature: NativeFeature, Member: ArchiveNode) -> None:
    ClassName = Member.ClassValue.NameValue
    if (
        Feature.kind != KMemberKinds[ClassName]
        or Feature.class_name not in ("", ClassName)
        or Feature.xml_tag != "Feature"
        or Feature.properties.get("Name") != ReadNativeName(Member)
    ):
        raise ValueError("owned presentation member has unqualified keyword semantics")
