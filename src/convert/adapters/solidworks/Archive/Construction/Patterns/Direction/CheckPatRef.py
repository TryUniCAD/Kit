from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the component and configuration must come from the actual part that allocated the selected plane
def CheckPatRef(
    SystemValue: PartSystem,
    Allocator: PersistentIds,
    PlaneValue: ArchiveNode,
    RoleValue: int,
) -> tuple[ArchiveNode, int, int]:
    RootValue = SystemValue.RootValue
    RequireRootNode(RootValue, "moPart_c")
    PlaneId = FieldInt(PlaneValue.FieldsValue, "f08")
    Geometry = ArchiveNode.RequireNode(PlaneValue.FieldsValue.get("f6f8"))
    if RoleValue:
        AxisValue = "x" if RoleValue == 1 else "y"
        if (
            RoleValue not in (1, 2)
            or SystemValue.SystemValues.PlaneValues.get(AxisValue) is not PlaneValue
            or sum(NodeValue is PlaneValue for NodeValue in SystemValue.FeatureValues)
            != 1
            or Geometry.FieldsValue.get("owner") is not None
        ):
            raise ValueError(
                "pattern direction must use its actual registered principal plane"
            )
    elif Geometry.FieldsValue.get("owner") is not PlaneValue:
        raise ValueError("pattern direction geometry must belong to the selected plane")
    if (
        PlaneValue.FieldsValue.get("owner") is not RootValue
        or not 0 <= PlaneId < 0x7FFFFFFF
        or Allocator.Allocations.get((PlaneValue, "f08")) != PlaneId
        or len(SystemValue.ConfigValues) != 1
    ):
        raise ValueError("pattern direction requires its actual allocated local plane")
    Config = SystemValue.ConfigValues[0]
    RequireRootNode(Config, "moPartConfiguration_c")
    UnitValue = ArchiveNode.RequireNode(RootValue.FieldsValue.get("f990"))
    RequireRootNode(UnitValue, "moUnitComponent_c")
    ConfigId = FieldInt(Config.FieldsValue, "f08")
    if (
        Config.FieldsValue.get("owner") is not RootValue
        or SystemValue.ManagerValue.FieldsValue.get("f360") is not Config
        or not 0 <= ConfigId < 0x7FFFFFFF
        or UnitValue.FieldsValue.get("owner") is not RootValue
        or FieldInt(UnitValue.FieldsValue, "has_ext") != 0
    ):
        raise ValueError("pattern direction requires the active local part component")
    return UnitValue, ConfigId, PlaneId
