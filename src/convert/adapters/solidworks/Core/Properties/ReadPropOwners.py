from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument


# scoped xml requires the native saved directory id and name on the same active part configuration
def ReadPropOwners(
    Document: CadDocument, Archive: SldprtArchive, VersionValue: int
) -> dict[int, str]:
    if len(Document.configurations) != 1:
        raise ValueError("part text requires one ordinary configuration")
    Directory = Archive.get("Contents/CMgrHdr2")
    if Directory is None:
        raise ValueError("part configuration properties require their saved directory")
    GraphValue = ReadMgrHeader(Directory, VersionValue)
    ListValue = CastValue(Mapping[str, object], GraphValue.RootValue.FieldsValue["f08"])
    RowsValue = CastValue(Sequence[Mapping[str, object]], ListValue["items"])
    if len(RowsValue) != 1:
        raise ValueError("part text requires one concrete saved configuration")
    Fields = ArchiveNode.RequireNode(RowsValue[0]["o"]).FieldsValue
    OwnerId, RawName = Fields["f30"], Fields["f10"]
    OwnerName = RawName.TextValue if isinstance(RawName, CStringValue) else RawName
    (ConfigValue,) = Document.configurations
    ActualId = ConfigValue.attributes.get("native_configuration_id")
    if (
        type(OwnerId) is not int
        or OwnerId < 0
        or type(OwnerName) is not str
        or not OwnerName.strip()
        or type(ActualId) is not int
        or ActualId != OwnerId
        or ConfigValue.name != OwnerName
        or ConfigValue.active is not True
        or Fields["f08"] != 1
        or Fields["f34"] != -1
    ):
        raise ValueError("part configuration properties differ from their native owner")
    LaneValue = f"Contents/Config-{OwnerId}"
    if not Archive.get(LaneValue) or not Archive.get(LaneValue + "-ResolvedFeatures"):
        raise ValueError("part configuration properties lack their physical part lanes")
    return {OwnerId: OwnerName}
