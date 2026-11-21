from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KRequiredMembers,
)
from convert.adapters.solidworks.Archive.Config.Members.MemberChecks import (
    KMemberChecks,
    KNodeChecks,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# null records must stay distinct from present managers with unqualified inherited objects
def CheckCfgMember(
    RootValue: ArchiveNode | None, MemberClass: RuntimeClass, MapValue: ArchiveMaps
) -> None:
    if RootValue is None:
        RoleName = KRequiredMembers.get(MemberClass)
        if RoleName is not None:
            raise BodyUnsupported(
                f"SOLIDWORKS {RoleName} member requires its concrete root"
            )
        return
    IndexValue = ObjectIndex(MapValue, RootValue)
    if (
        RootValue.ClassValue != MemberClass
        or IndexValue is None
        or IndexValue < MapValue.BaseValue
    ):
        raise BodyUnsupported(
            "SOLIDWORKS configuration member requires a new root object"
        )
    CheckNode = KNodeChecks.get(MemberClass)
    if CheckNode is not None:
        CheckNode(RootValue)
    CheckOwned = KMemberChecks.get(MemberClass)
    if CheckOwned is not None:
        CheckOwned(RootValue, MapValue)
