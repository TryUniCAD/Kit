from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeAsmOptions import (
    MakeAsmOptions,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeCompState import (
    MakeCompState,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.MakeCfgSeeds import (
    MakeCfgSeeds,
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
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the assembly configuration uses the common qualified base plus its actual option profiles and componentless native initial state
def MakeAsmConfig(
    InputValue: ConfigSpec, OwnerValue: ArchiveNode, TargetValue: FeatureTarget
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moAssembly_c")
    NodeValue = ArchiveNode(RuntimeClass("moConfiguration_c", 1), {})
    InitFeatureMut(NodeValue, InputValue.NameValue, OwnerValue, TargetValue)
    NodeValue.FieldsValue.update(MakeCfgSeeds(InputValue, TargetValue.FileVersion))
    NodeValue.FieldsValue.update(
        {
            "f08": 0,
            "fc48": MakeAsmOptions(),
            "fc50": MakeAsmOptions(),
            "fca0": None,
            "fca8": None,
            "fce8": [{"o": MakeCompState()}],
            "fba8": None,
            "fbb0": None,
            "fbc0": 0,
            "fbc4": 1,
            "fbc8": None,
            "fce0": None,
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
