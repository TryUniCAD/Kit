from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KFeatColorClass,
    KRelMgrClass,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckRelMember import (
    CheckRelMember,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# only the observed color member can complete as null without allocating an object
def CheckCfgMember(
    RootValue: ArchiveNode | None, MemberClass: RuntimeClass, MapValue: ArchiveMaps
) -> None:
    if RootValue is None:
        if MemberClass != KFeatColorClass:
            raise BodyUnsupported(
                "SOLIDWORKS relation member requires its concrete root"
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
    if MemberClass == KRelMgrClass:
        CheckRelMember(RootValue)
