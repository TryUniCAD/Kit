from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinWallOwner import (
    ThinWallOwner,
)


# all local angle and thickness owners must be the actual distinct linked nodes
def CheckThinDims(
    NodesValue: tuple[ArchiveNode, ...],
    AngleValue: RevolveAngle,
    FirstValue: ThinWallOwner,
    SecondValue: ThinWallOwner,
) -> None:
    DriverNodes = tuple(
        ItemValue
        for Driver in (AngleValue, FirstValue, SecondValue)
        for ItemValue in (Driver.DisplayValue, Driver.HandleValue, Driver.DimensionValue, Driver.ParameterValue)
    )
    CountsValue = Counter(ItemValue.ClassValue.NameValue for ItemValue in DriverNodes)
    LinkedNodes = tuple(ItemValue for ItemValue in NodesValue if ItemValue.ClassValue.NameValue in CountsValue)
    DimensionIds = {Driver.DimensionValue.FieldsValue["f50"] for Driver in (AngleValue, FirstValue, SecondValue)}
    if len(set(DriverNodes)) != len(DriverNodes) or len(DimensionIds) != 3 or set(LinkedNodes) != set(DriverNodes):
        raise ValueError("SOLIDWORKS thin end and thickness owners are detached or aliased")
