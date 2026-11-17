from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# selected feature references use their actual first creation event or the independently mapped native unset epoch
def DatumTime(Header: ArchiveNode, DatumId: int) -> int:
    LogsValue = ReadRows(FieldRecord(Header.FieldsValue.get("f20")).get("items"))
    Matches = tuple(
        FieldRecord(Value.get("o"))
        for Value in LogsValue
        if FieldInt(FieldRecord(Value.get("o")), "f48") == DatumId
    )
    if len(Matches) > 1:
        raise ValueError("child datum has ambiguous creation logs")
    Events = ReadRows(Matches[0].get("items")) if Matches else ()
    EpochValue = FieldInt(FieldRecord(Events[0].get("o")), "f18") if Events else 2592000
    if not 0 <= EpochValue <= 0xFFFFFFFF:
        raise ValueError("datum creation epoch exceeds native unsigned time")
    return EpochValue
