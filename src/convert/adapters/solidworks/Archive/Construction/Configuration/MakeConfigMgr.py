from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigFieldSets import (
    KManagerArrays,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.MakePartConfig import (
    MakePartConfig,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import (
    ManagerInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the independent manager graph must retain its selected configuration aliases without consuming global model feature identifiers
def MakeConfigMgr(
    InputValue: ManagerInput, OwnerValue: ArchiveNode, TargetValue: FeatureTarget
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    if type(InputValue) is not ManagerInput:
        raise TypeError("part configuration manager requires typed explicit inputs")
    NodeValue = ArchiveNode(RuntimeClass("moConfigurationMgr_c", 1), {})
    InitFeatureMut(NodeValue, InputValue.NameValue, OwnerValue, TargetValue)
    ConfigValues = tuple(
        MakePartConfig(ItemValue, OwnerValue, IndexValue, TargetValue)
        for IndexValue, ItemValue in enumerate(InputValue.ConfigValues)
    )
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(
        {
            "f360": ConfigValues[InputValue.CurrentIndex],
            "f368": ConfigValues[InputValue.CurrentIndex],
            "f40c": len(ConfigValues),
            "f370": {
                "n": len(ConfigValues),
                "items": [{"o": ItemValue} for ItemValue in ConfigValues],
            },
            "f55c": 0,
            "f578": "",
            "f5b0": ArchiveNode(RuntimeClass("suObList", 1), {"n": 0, "items": []}),
            "f658": 0,
            "f6d0": None,
            "f730": {"n": 0, "items": []},
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
        FieldsValue[CountName] = 0
        FieldsValue[FieldName] = []
    ClearSystemMut(NodeValue)
    return NodeValue
