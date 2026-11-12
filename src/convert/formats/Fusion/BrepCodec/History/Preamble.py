from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakePreamble(History: HistoryState) -> GeometryRecord:
    return GeometryRecord(
        "history_stream",
        (
            History.Generation,
            History.Generation,
            0,
            History.Allocation,
            EntityRef(-1),
            EntityRef(0),
            EntityRef(1),
            EntityRef(-1),
        ),
    )
