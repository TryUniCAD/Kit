from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.WidthDepthLink import (
    WidthDepthLink,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# a derived body needs complete typed model streams and an unambiguous active configuration
def CheckGeometry(
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ModelValue: NativeModel,
    *,
    RelationValue: WidthDepthLink | None = None,
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
    EquationsValue = ModelValue.equations
    if (
        ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or (EquationsValue and RelationValue is None)
        or (
            RelationValue is not None
            and (
                RelationValue is not ModelValue.WidthDepth
                or RelationValue.LinkValue is not LinkValue
                or len(EquationsValue) != 1
                or EquationsValue[0].configuration_id != 0
                or EquationsValue[0].source != RelationValue.SourceText
            )
        )
    ):
        raise ValueError(
            "cache free part has unsupported configuration or equation intent"
        )
