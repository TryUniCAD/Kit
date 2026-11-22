from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeAsmConfig import (
    MakeAsmConfig,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigFieldSets import (
    KManagerArrays,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the first ordinary assembly manager publishes one independent active configuration without consuming global persistent feature identifiers
def MakeAsmManager(
    NameValue: str,
    ConfigValue: ConfigSpec,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
) -> ArchiveNode:
    CurrentValue = MakeAsmConfig(ConfigValue, OwnerValue, TargetValue)
    NodeValue = ArchiveNode(RuntimeClass("moConfigurationMgr_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue)
    NodeValue.FieldsValue.update(
        {
            "f360": CurrentValue,
            "f368": CurrentValue,
            "f40c": 1,
            "f370": {"n": 1, "items": [{"o": CurrentValue}]},
            "f55c": 0,
            "f578": "",
            "f5b0": ArchiveNode(RuntimeClass("suObList", 1), EmptyRootRows()),
            "f658": 0,
            "f6d0": None,
            "f730": EmptyRootRows(),
            "f758": 0,
            "f75c": 2,
            "f810": "",
            "f818": 0,
            "f81c": 0,
            "f830": 0xFFFFFFFF,
            "f860": 0,
            "has8a0": 0,
        }
    )
    for CountName, FieldName in KManagerArrays:
        NodeValue.FieldsValue[CountName] = 0
        NodeValue.FieldsValue[FieldName] = []
    ClearSystemMut(NodeValue)
    return NodeValue
