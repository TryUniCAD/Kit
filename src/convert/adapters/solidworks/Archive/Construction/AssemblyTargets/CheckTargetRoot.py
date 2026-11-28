from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# recursive placement must reject mismatched graph headers managers or file kinds before deriving any parent reference state
def CheckTargetRoot(TargetValue: TargetDocument) -> None:
    ClassName = TargetValue.RootValue.ClassValue.NameValue
    if ClassName not in ("moPart_c", "moAssembly_c"):
        raise ValueError(
            "ordinary generated targets require a concrete part or assembly"
        )
    KindValue = 2 if ClassName == "moPart_c" else 3
    ConfigClass = "moPartConfiguration_c" if KindValue == 2 else "moConfiguration_c"
    for NodeValue, ExpectedClass in (
        (TargetValue.RootValue, ClassName),
        (TargetValue.ManagerValue, "moConfigurationMgr_c"),
        (TargetValue.CurrentConfig, ConfigClass),
        (TargetValue.HeaderValue, "moHeader_c"),
        (TargetValue.TopHeader, "moHeader_c"),
        (TargetValue.ManagerHeader, "dmConfigMgrHeader_c"),
    ):
        RequireRootNode(NodeValue, ExpectedClass)
    if (
        TargetValue.ConfigValue.RootValue is not TargetValue.RootValue
        or TargetValue.ConfigValue.HeaderValue is not TargetValue.HeaderValue
        or TargetValue.ConfigValue.VersionValue != 19000
        or TargetValue.ResolvedValue.VersionValue != 19000
        or TargetValue.ManagerValue.FieldsValue["f360"] is not TargetValue.CurrentConfig
        or TargetValue.ManagerValue.FieldsValue["f368"] is not TargetValue.CurrentConfig
        or TargetValue.CurrentConfig.FieldsValue.get("owner")
        is not TargetValue.RootValue
    ):
        raise ValueError("generated target lost its actual linked configuration owners")
    FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
    if (
        TargetValue.TopHeader.FieldsValue["f38"] is not FileValue
        or ReadFileKey(FileValue)[2] != KindValue
        or not TargetValue.HeaderValue.FieldsValue["fec"]
        or TargetValue.TopHeader.FieldsValue["fec"]
    ):
        raise ValueError(
            "generated target headers disagree on file kind or model presence"
        )
