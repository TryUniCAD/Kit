from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
)


# selected feature references use their actual first creation event or the independently mapped native unset epoch
def DatumTime(Header: ArchiveNode, DatumId: int) -> int:
    LogsValue = ReadLogItems(Header.FieldsValue.get("f20"), "moLogs_c")
    Matches = tuple(
        Value for Value in LogsValue if FieldInt(Value.FieldsValue, "f48") == DatumId
    )
    if len(Matches) > 1:
        raise ValueError("child datum has ambiguous creation logs")
    Events = ReadLogItems(Matches[0], "moStamp_c") if Matches else ()
    EpochValue = FieldInt(Events[0].FieldsValue, "f18") if Events else 2592000
    if not 0 <= EpochValue <= 0xFFFFFFFF:
        raise ValueError("datum creation epoch exceeds native unsigned time")
    return EpochValue
