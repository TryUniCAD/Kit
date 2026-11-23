from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireRecord,
)


# metadata names must describe the one actual configuration whose manager and model own the serialized assembly
def InfoConfigName(StateValue: AssemblyState) -> str:
    ManagerValue = StateValue.ManagerValue
    ConfigValue = StateValue.CurrentConfig
    RequireRootNode(ManagerValue, "moConfigurationMgr_c")
    RequireRootNode(ConfigValue, "moConfiguration_c")
    FieldsValue = ManagerValue.FieldsValue
    ConfigList = RequireRecord(FieldsValue.get("f370"))
    RowsValue = ReadRows(ConfigList.get("items"))
    if (
        ManagerValue.FieldsValue.get("owner") is not StateValue.RootValue
        or ConfigValue.FieldsValue.get("owner") is not StateValue.RootValue
        or len(RowsValue) != 1
        or FieldInt(ConfigList, "n") != 1
        or RowsValue[0].get("o") is not ConfigValue
        or FieldsValue.get("f360") is not ConfigValue
        or FieldsValue.get("f368") is not ConfigValue
    ):
        raise ValueError(
            "assembly information requires the actual sole active configuration"
        )
    return ReadNodeName(ConfigValue)
