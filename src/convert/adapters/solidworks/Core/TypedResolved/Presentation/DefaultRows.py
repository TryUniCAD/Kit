from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

# english labels come from native resources while light multiplicity is the measured session default profile
KDefaultMembers = {
    "moDetailCabinet_c": (
        ("notes.head", "Notes", "moNotesAreaFtrFolder_c"),
        ("notes.end", "Notes1___EndTag___", "moNotesAreaFtrFolder_c"),
    ),
    "moEnvFolder_c": (
        ("light.ambient", "Ambient", "moAmbientLight_c"),
        ("light.directional.1", "Directional1", "moDirectionLight_c"),
        ("light.directional.2", "Directional2", "moDirectionLight_c"),
        ("light.directional.3", "Directional3", "moDirectionLight_c"),
    ),
}


# runtime defaults have owner role identities without invented native object numbers or saved state
def MakeDefaultRows(OwnerValue: ArchiveNode) -> tuple[Mapping[str, object], ...]:
    OwnerId = NativeNodeId(OwnerValue)
    return tuple(
        {
            "id": f"sldprt:system:{OwnerId}:{RoleValue}",
            "native_object_id": None,
            "name": NameValue,
            "type": ClassName.removeprefix("mo").removesuffix("_c"),
            "class": ClassName,
            "parent_id": f"sldprt:feature:{OwnerId}",
            "parent": ReadNativeName(OwnerValue),
            "owner_role": RoleValue,
            "source": "implicit_runtime_default_profile",
            "typed_archive_owner": None,
            "state": None,
        }
        for RoleValue, NameValue, ClassName in KDefaultMembers[
            OwnerValue.ClassValue.NameValue
        ]
    )
