from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ProjectCmgrRows import ProjectCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut


# compatibility readers need an honest typed dependency result without admitting the remaining linked graph
def ReadCmgrInfo(BufferValue: bytes, VersionValue: int | None) -> Mapping[str, object]:
    UsageValue = BodyUsage()
    try:
        if VersionValue is None:
            raise ValueError("SOLIDWORKS manager archive version is unavailable")
        GraphValue = ReadCmgrMut(BufferValue, VersionValue, UsageValue=UsageValue)
        RowsValue = ProjectCmgrRows(GraphValue.RootValue)
    except (TypeError, ValueError, KeyError) as ErrorInfo:
        return {
            "status": "unsupported",
            "archive_version": VersionValue,
            "diagnostic": str(ErrorInfo),
            "usage": GetBodyReport(UsageValue),
            "full_linked_graph": False,
        }
    return {
        "status": "complete",
        "archive_version": VersionValue,
        "map_base": 1,
        "map_counter": GraphValue.MapValue.CounterValue,
        "configuration_count": len(RowsValue),
        "configurations": RowsValue,
        "resolved_body_mapping_context": GraphValue.RootValue.FieldsValue["f658"],
        "usage": GraphValue.ReportValue,
        "full_linked_graph": False,
    }
