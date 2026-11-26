from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


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
