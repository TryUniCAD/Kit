from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireRecord,
)


# a registered default datum may use the documented unset creation epoch before its first recorded event
def ReadPatTime(
    Header: ArchiveNode, PlaneValue: ArchiveNode, PlaneId: int, *, DefaultDatum: bool
) -> tuple[int, bool]:
    LogsValue = ReadLogItems(Header.FieldsValue.get("f20"), "moLogs_c")
    Matches = tuple(
        ItemValue
        for ItemValue in LogsValue
        if FieldInt(ItemValue.FieldsValue, "f48") == PlaneId
    )
    if DefaultDatum and not Matches:
        return DatumTime(Header, PlaneId), False
    if (
        len(Matches) != 1
        or Matches[0].FieldsValue.get("f50")
        != CStringValue(ReadNodeName(PlaneValue), True)
        or not ReadLogItems(Matches[0], "moStamp_c")
    ):
        raise ValueError("pattern direction requires both actual plane creation logs")
    return DatumTime(Header, PlaneId), True


# the two header roles bind the same selected configuration and earlier plane allocation
def CheckPatTime(
    Headers: tuple[ArchiveNode, ArchiveNode],
    PlaneValue: ArchiveNode,
    PlaneId: int,
    ConfigId: int,
    CreatedAt: int,
    *,
    DefaultDatum: bool,
) -> tuple[int, int]:
    Primary, Secondary = Headers
    RequireRootNode(Primary, "moHeader_c")
    RequireRootNode(Secondary, "moHeader_c")
    SelfValue = ArchiveNode.RequireNode(Primary.FieldsValue.get("f38"))
    RequireRootNode(SelfValue, "moExtObject_c")
    if (
        tuple(FieldInt(Value.FieldsValue, "fec") for Value in Headers) != (1, 0)
        or Secondary.FieldsValue.get("f38") is not SelfValue
        or FieldInt(RequireRecord(SelfValue.FieldsValue.get("refcfg")), "f10")
        != ConfigId
        or not PlaneId
        < FieldInt(Primary.FieldsValue, "f08")
        == FieldInt(Secondary.FieldsValue, "f08")
    ):
        raise ValueError("pattern direction requires paired local part headers")
    PrimaryTime = ReadPatTime(Primary, PlaneValue, PlaneId, DefaultDatum=DefaultDatum)
    SecondaryTime = ReadPatTime(
        Secondary, PlaneValue, PlaneId, DefaultDatum=DefaultDatum
    )
    Epoch, _ = PrimaryTime
    if PrimaryTime != SecondaryTime or (not DefaultDatum and Epoch != CreatedAt):
        raise ValueError("pattern direction creation differs between its own headers")
    return Epoch, SignedStamp(FieldInt(Primary.FieldsValue, "f40"))
