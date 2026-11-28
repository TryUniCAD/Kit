from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadNodeName,
    RequireNode,
)


# the part self row requires both real header roots and the selected ordinary part configuration
def ReadSelfOwners(
    SystemValue: PartSystem, HeadersValue: tuple[ArchiveNode, ArchiveNode]
) -> tuple[ArchiveNode, ArchiveNode]:
    RootValue = RequireNode(SystemValue.RootValue, "moPart_c")
    Header, TopHeader = (RequireNode(Value, "moHeader_c") for Value in HeadersValue)
    ModelFields = RootValue.FieldsValue
    UnitValue = RequireNode(ModelFields["f990"], "moUnitComponent_c")
    (ConfigValue,) = SystemValue.ConfigValues
    Config = RequireNode(ConfigValue, "moPartConfiguration_c")
    Manager = RequireNode(SystemValue.ManagerValue, "moConfigurationMgr_c").FieldsValue
    if (
        Header is TopHeader
        or Header.FieldsValue["fec"] != 1
        or TopHeader.FieldsValue["fec"] != 0
        or Header.FieldsValue["f38"] is not TopHeader.FieldsValue["f38"]
        or Header.FieldsValue["f08"] != TopHeader.FieldsValue["f08"]
        or UnitValue.FieldsValue != {"owner": RootValue, "has_ext": 0}
        or Config.FieldsValue["owner"] is not RootValue
        or Config.FieldsValue["f08"] != 0
        or ReadNodeName(Config) != "Default"
        or any(Manager[FieldName] is not Config for FieldName in ("f360", "f368"))
    ):
        raise ValueError(
            "part self visibility requires the actual headers and selected Default owner"
        )
    return UnitValue, Config
