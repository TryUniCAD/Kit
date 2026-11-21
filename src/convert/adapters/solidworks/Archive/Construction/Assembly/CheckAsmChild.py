from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# assembly composition must consume the actual complete generated child profile and its independent header manager and selected configuration owners
def CheckAsmChild(ChildValue: PartCandidate) -> None:
    for NodeValue, ClassName in (
        (ChildValue.SystemValue.RootValue, "moPart_c"),
        (ChildValue.HeaderValue, "moHeader_c"),
        (ChildValue.TopHeader, "moHeader_c"),
        (ChildValue.ManagerHeader, "dmConfigMgrHeader_c"),
        (ChildValue.SystemValue.ManagerValue, "moConfigurationMgr_c"),
        (ChildValue.CurrentConfig, "moPartConfiguration_c"),
    ):
        RequireRootNode(NodeValue, ClassName)
    if (
        ChildValue.ConfigValue.RootValue is not ChildValue.SystemValue.RootValue
        or ChildValue.SystemValue.ManagerValue.FieldsValue["f368"]
        is not ChildValue.CurrentConfig
        or len(ChildValue.SystemValue.ConfigValues) != 1
    ):
        raise ValueError(
            "assembly child requires the actual complete single active part configuration"
        )
    if (
        not ChildValue.HeaderValue.FieldsValue["fec"]
        or ChildValue.TopHeader.FieldsValue["fec"]
        or ChildValue.HeaderValue.FieldsValue["f08"]
        != ChildValue.TopHeader.FieldsValue["f08"]
    ):
        raise ValueError(
            "assembly child headers disagree on actual model presence or allocation"
        )
