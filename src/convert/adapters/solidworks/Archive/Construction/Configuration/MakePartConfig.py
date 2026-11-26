from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.MakeCfgSeeds import (
    MakeCfgSeeds,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.PartCfgObject import (
    PartCfgObject,
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


# part configurations allocate local manager identifiers and never consume a global persistent feature identifier
def MakePartConfig(
    InputValue: ConfigSpec,
    OwnerValue: ArchiveNode,
    LocalId: int,
    TargetValue: FeatureTarget,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    if (
        type(InputValue) is not ConfigSpec
        or type(LocalId) is not int
        or not 0 <= LocalId < 0x7FFFFFFF
    ):
        raise ValueError(
            "part configuration requires typed intent and a nonnegative local identifier"
        )
    NodeValue = ArchiveNode(RuntimeClass("moPartConfiguration_c", 1), {})
    InitFeatureMut(NodeValue, InputValue.NameValue, OwnerValue, TargetValue)
    NodeValue.FieldsValue.update(MakeCfgSeeds(InputValue, TargetValue.FileVersion))
    NodeValue.FieldsValue.update(
        {
            "f08": LocalId,
            "fc60": 0,
            "fcc8": 0,
            "fc64": 0,
            "ndc8_hi": 0,
            "ndc8_lo": 0,
            "fca8": [],
            "fce8": [],
            "fd20": [],
            "fdc8": [],
            "nca8": 0,
            "nce8": 0,
            "nd20": 0,
            "f4d0": PartCfgObject(),
            "fc50": -1.0,
            "fc48": None,
            "fcb8": None,
            "fcc0": None,
            "fccc": -1,
            "fcd4": -1,
            "fcd0": -1,
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
