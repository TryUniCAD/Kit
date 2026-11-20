from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KManagerClass,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ManagerHeader.MakeMgrEntry import (
    MakeMgrEntry,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ManagerHeader.SelectMgrCfg import (
    SelectMgrCfg,
)
from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import FieldInt
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the manager header owns a fresh directory graph and its explicit save event
def MakeMgrHeader(ManagerValue: ArchiveNode, SavedAt: int) -> ArchiveNode:
    RequireRootNode(ManagerValue, "moConfigurationMgr_c")
    OwnerValue = ArchiveNode.RequireNode(ManagerValue.FieldsValue["owner"])
    RequireRootNode(OwnerValue, "moPart_c")
    if type(SavedAt) is not int or not 0 <= SavedAt <= 0xFFFFFFFF:
        raise ValueError("manager save event must fit unsigned unix seconds")
    ConfigValue = SelectMgrCfg(ManagerValue, OwnerValue)
    return ArchiveNode(
        KManagerClass,
        {
            "f08": {"n": 1, "items": [{"o": MakeMgrEntry(ConfigValue, OwnerValue)}]},
            "f60": SavedAt,
            "f68": FieldInt(ManagerValue.FieldsValue, "f75c"),
        },
    )
