from convert.adapters.solidworks.Archive.Construction.Configuration.Events.ConfigEvent import (
    ConfigEvent,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import (
    ReadMemberTime,
)


# source creation provenance and feature moments must retain their actual owner instead of using the document save target
def ReadCfgEvent(NodeValue: ArchiveNode) -> ConfigEvent:
    NodeValue = ArchiveNode.RequireNode(NodeValue)
    if NodeValue.ClassValue.NameValue not in (
        "moConfigurationMgr_c",
        "moPartConfiguration_c",
    ):
        raise ValueError(
            "configuration events require their actual native feature owners"
        )
    RequireRootNode(NodeValue, NodeValue.ClassValue.NameValue)
    FieldsValue = NodeValue.FieldsValue
    if (
        FieldInt(FieldsValue, "f29c") != 101
        or FieldInt(FieldsValue, "f2b8") != 0
        or FieldInt(FieldsValue, "f2bc") != 0
    ):
        raise ValueError("configuration event has unrepresented update provenance")
    return ConfigEvent(
        ReadMemberTime(NodeValue),
        FeatureTarget(
            DateCode=FieldInt(FieldsValue, "f2b4"),
            ParasolidVersion=FieldInt(FieldsValue, "f2ac"),
            FileVersion=FieldInt(FieldsValue, "f2b0"),
            ServicePack=FieldInt(FieldsValue, "f300"),
            SubservicePack=FieldInt(FieldsValue, "f301"),
        ),
    )
