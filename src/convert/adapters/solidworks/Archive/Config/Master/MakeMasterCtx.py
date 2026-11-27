from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Master.MasterLayout import (
    KMasterClass,
    KMasterLayouts,
    KMasterVirtuals,
)
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a caller must supply the actual inherited part at the ordinary resolved boundary
def MakeMasterCtx(
    VersionValue: int, PartValue: ArchiveNode, MapValue: ArchiveMaps
) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != KHeaderVersion:
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master requires archive version 19000"
        )
    OwnerIndex = ObjectIndex(MapValue, PartValue)
    if (
        PartValue.ClassValue != KPartRoot
        or OwnerIndex is None
        or OwnerIndex != PartValue.IndexValue
        or OwnerIndex >= MapValue.BaseValue
        or MapValue.EntryMap[OwnerIndex].EntryValue is not PartValue
    ):
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master requires the inherited part owner"
        )
    return BodyContext(
        VersionValue,
        KMasterLayouts,
        KMasterVirtuals,
        {KMasterClass.NameValue: (KMasterClass.SchemaValue,)},
        PartRootValue=PartValue,
    )
