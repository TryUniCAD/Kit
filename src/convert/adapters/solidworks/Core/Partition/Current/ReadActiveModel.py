from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadActiveSolid import (
    ReadActiveSolid,
)
from convert.adapters.solidworks.Core.Partition.Current.ReadShadowModel import (
    ReadShadowModel,
)
from interchange.brep.Topology.BrepModel import BrepModel


# successful general and fin shadow reads stay authoritative before additional typed recovery
def ReadActiveModel(DataValue: bytes) -> BrepModel | None:
    ModelValue = DecodeBrep(DataValue)
    if ModelValue is not None:
        return ModelValue
    ModelValue = ReadShadowModel(DataValue)
    if ModelValue is not None:
        return ModelValue
    try:
        return ReadActiveSolid(DataValue)
    except (KeyError, ValueError, OverflowError):
        return None
