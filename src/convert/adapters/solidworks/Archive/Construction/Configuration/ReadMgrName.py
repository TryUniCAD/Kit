from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldText


# source manager name absence must remain distinct from an empty name object or a missing field
def ReadMgrName(ManagerValue: ArchiveNode) -> str | None:
    RequireRootNode(ManagerValue, "moConfigurationMgr_c")
    if "f18" not in ManagerValue.FieldsValue:
        raise ValueError("configuration manager lacks its actual name field")
    NameValue = ManagerValue.FieldsValue["f18"]
    if NameValue is None:
        return None
    NameNode = ArchiveNode.RequireNode(NameValue)
    RequireRootNode(NameNode, "moNodeName_c")
    TextValue = FieldText(NameNode.FieldsValue, "f08")
    if not ReadStyleText(TextValue, "configuration manager name"):
        raise ValueError("configuration manager name must not be empty")
    return TextValue
