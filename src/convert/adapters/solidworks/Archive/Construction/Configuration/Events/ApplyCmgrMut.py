from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import (
    MakeFeatTime,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.CmgrEvents import (
    CmgrEvents,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.RequireCmgr import (
    RequireCmgr,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# constructor composition supplies known provenance and precise moments before the independent manager stream is emitted
def ApplyCmgrMut(
    SystemValue: PartSystem, InputValue: CmgrEvents, TargetValue: FeatureTarget
) -> None:
    if (
        type(SystemValue) is not PartSystem
        or type(InputValue) is not CmgrEvents
        or type(TargetValue) is not FeatureTarget
    ):
        raise ValueError("manager event construction requires typed fresh graph inputs")
    RequireRootNode(SystemValue.RootValue, "moPart_c")
    ActiveValue = RequireCmgr(SystemValue.ManagerValue)
    if (
        len(SystemValue.ConfigValues) != 1
        or SystemValue.ConfigValues[0] is not ActiveValue
    ):
        raise ValueError("manager event requires the actual constructed configuration")
    PendingValues: list[dict[str, int]] = []
    for NodeValue, EventValue in (
        (SystemValue.ManagerValue, InputValue.ManagerValue),
        (ActiveValue, InputValue.ActiveValue),
    ):
        FieldsValue = NodeValue.FieldsValue
        CreatedBy = EventValue.CreatedBy
        if FieldsValue.get("owner") is not SystemValue.RootValue or any(
            FieldInt(FieldsValue, FieldName) != ExpectedValue
            for FieldName, ExpectedValue in (
                ("f29c", 101),
                ("f2a0", 0),
                ("f2a4", 0),
                ("f2b8", 0),
                ("f2bc", 0),
                ("f2b0", TargetValue.FileVersion),
                ("f2b4", TargetValue.DateCode),
                ("f2ac", TargetValue.ParasolidVersion),
                ("f300", TargetValue.ServicePack),
                ("f301", TargetValue.SubservicePack),
            )
        ):
            raise ValueError(
                "manager event requires untouched fresh feature provenance"
            )
        if (
            CreatedBy.FileVersion != TargetValue.FileVersion
            or CreatedBy.DateCode != TargetValue.DateCode
            or CreatedBy.ParasolidVersion != TargetValue.ParasolidVersion
            or CreatedBy.ServicePack != TargetValue.ServicePack
        ):
            raise ValueError("source manager creation profile differs from the target")
        PendingValues.append(
            dict(
                MakeFeatTime(EventValue.MomentValue),
                f2b0=CreatedBy.FileVersion,
                f2b4=CreatedBy.DateCode,
                f2ac=CreatedBy.ParasolidVersion,
                f300=CreatedBy.ServicePack,
                f301=CreatedBy.SubservicePack,
            )
        )
    for NodeValue, EventFields in zip(
        (SystemValue.ManagerValue, ActiveValue), PendingValues, strict=True
    ):
        NodeValue.FieldsValue.update(EventFields)
