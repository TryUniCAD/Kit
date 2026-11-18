from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeCompState import (
    MakeCompState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeExtFeature import (
    MakeExtFeature,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeRefChain import (
    MakeRefChain,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# per occurrence assembly configuration state owns its contextual containing file while selecting the actual generated child configuration separately
def MakeOccConfig(Reference: ArchiveNode, ConfigValue: ArchiveNode) -> ArchiveNode:
    External = ArchiveNode.RequireNode(Reference.FieldsValue["f4f8"])
    SharedValue = FieldRecord(External.FieldsValue["f10"])
    TargetValue = MakeExtFeature(Reference, SharedValue, False)
    ContextFile = ArchiveNode(
        RuntimeClass("moExtObject_c", 1),
        {
            "shared": SharedValue,
            "f48": 0,
            "f4c": 1,
            "f50": 0,
            "f54": 0,
            "f58": 0,
            "f60": 0,
            "f70": 0,
            "f78": -1,
            "refcfg": {
                "f08": ReadNodeName(ConfigValue),
                "f10": ConfigValue.FieldsValue["f08"],
            },
        },
    )
    Component = ArchiveNode(
        RuntimeClass("moContextChainComponent_c", 1),
        {
            "owner": None,
            "f20": MakeRefChain(TargetValue),
            "f30": (101 + FieldInt(Reference.FieldsValue, "f3f0")) & 0xFFFFFFFF,
            "f40": ContextFile,
            "f48": 0,
        },
    )
    OptionsValue = ArchiveNode.RequireNode(ConfigValue.FieldsValue["fc50"])
    OptionsCopy = ArchiveNode(
        RuntimeClass("moConfig_c", 1), dict(OptionsValue.FieldsValue)
    )
    OptionsCopy.FieldsValue["f64"] = 0
    NodeValue = MakeCompState()
    NodeValue.FieldsValue.update(
        {
            "f08": OptionsCopy,
            "f10": Component,
            "f28": dict(FieldRecord(Reference.FieldsValue["f3c0"])),
        }
    )
    return NodeValue
