from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
    KManagerClass,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadRows,
    RequireRecord,
)


# the current independent part configuration must be the actual selected manager row
def SelectMgrCfg(ManagerValue: ArchiveNode, OwnerValue: ArchiveNode) -> ArchiveNode:
    ListFields = RequireRecord(ManagerValue.FieldsValue["f370"])
    RowsValue = ReadRows(ListFields["items"])
    if (
        len(RowsValue) != 1
        or FieldInt(ListFields, "n") != 1
        or FieldInt(ManagerValue.FieldsValue, "f40c") != 1
    ):
        raise ValueError(
            "fresh manager header requires one actual independent configuration"
        )
    ConfigValue = ArchiveNode.RequireNode(RowsValue[0]["o"])
    RequireRootNode(ConfigValue, "moPartConfiguration_c")
    Values = ConfigValue.FieldsValue
    if (
        Values.get("owner") is not OwnerValue
        or ManagerValue.FieldsValue["f360"] is not ConfigValue
        or ManagerValue.FieldsValue["f368"] is not ConfigValue
        or Values["f6a0"] is not None
    ):
        raise ValueError(
            "manager header requires the actual owning part and active independent configuration"
        )
    if Values.get("fbe0", 0) or Values.get("fbf0", 0) or Values["f2f0"] is not None:
        raise ValueError(
            "manager header does not admit excluded configurations or comment sidecars"
        )
    return ConfigValue


# lightweight entries derive the name and save state from the chosen configuration and part
def MakeMgrEntry(ConfigValue: ArchiveNode, OwnerValue: ArchiveNode) -> ArchiveNode:
    Values = ConfigValue.FieldsValue
    NameNode = ArchiveNode.RequireNode(Values["f18"])
    NameValue = FieldText(NameNode.FieldsValue, "f08")
    Description = ReadStyleText(Values["f1f8"], "configuration description")
    return ArchiveNode(
        KConfigHdrClass,
        {
            "f08": 1,
            "f10": NameValue,
            "f30": FieldInt(Values, "f08"),
            "f38": FieldInt(Values, "f860"),
            "f18": Description or NameValue,
            "f34": -1,
            "f40": int(
                FieldInt(Values, "f968") != 1 and bool(FieldInt(Values, "f0c") & 8)
            ),
            "f20": ReadStyleText(Values["f4a8"], "configuration comment"),
            "f28": ReadStyleText(Values["f498"], "configuration alternate name"),
            "f44": FieldInt(Values, "f4c4"),
            "f48": FieldInt(Values, "fbd0"),
            "f50": FieldInt(OwnerValue.FieldsValue, "f1300"),
            "f4c": 101,
        },
    )


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
            "f08": {"items": ({"o": MakeMgrEntry(ConfigValue, OwnerValue)},)},
            "f60": SavedAt,
            "f68": FieldInt(ManagerValue.FieldsValue, "f75c"),
        },
    )
