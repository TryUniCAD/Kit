from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# a derived body needs complete typed model streams and an unambiguous active configuration
def CheckGeometry(
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ModelValue: NativeModel,
) -> None:
    Reports = (
        LinkValue.ConfigValue.ReportValue,
        LinkValue.ResolvedValue.ReportValue,
        ManagerValue.ReportValue,
    )
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in Reports
    ):
        raise ValueError(
            "cache free part requires complete nonprovisional native grammar"
        )
    if (
        ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or ModelValue.equations
    ):
        raise ValueError(
            "cache free part has unsupported configuration or equation intent"
        )
