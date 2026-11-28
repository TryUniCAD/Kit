from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrIntent import (
    ReadMgrIntent,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# a manager event can address only the actual selected directory configuration rather than an equal name or identifier
def RequireCmgr(ManagerValue: ArchiveNode) -> ArchiveNode:
    RequireRootNode(ManagerValue, "moConfigurationMgr_c")
    IntentValue = ReadMgrIntent(ManagerValue)
    if (
        FieldInt(ManagerValue.FieldsValue, "f08") != -1
        or len(IntentValue.ConfigValues) != 1
        or IntentValue.CurrentIndex != 0
    ):
        raise ValueError(
            "configuration events require the ordinary single local manager"
        )
    ActiveValue = ArchiveNode.RequireNode(ManagerValue.FieldsValue.get("f360"))
    RequireRootNode(ActiveValue, "moPartConfiguration_c")
    if ActiveValue is ManagerValue:
        raise ValueError(
            "manager and active configuration must be distinct actual owners"
        )
    return ActiveValue
