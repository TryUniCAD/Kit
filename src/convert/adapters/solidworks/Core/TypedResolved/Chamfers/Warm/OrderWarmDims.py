from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)


# saved angle display inventory may reverse while the authoritative live slots keep their roles
def OrderWarmDims(
    Dimensions: tuple[NativeDimension, ...], Owners: ChmfOwners
) -> tuple[NativeDimension, ...]:
    Wanted = tuple(Value.NameValue for Value in Owners.DriversValue)
    Actual = tuple(Value.name for Value in Dimensions)
    if Owners.ModeWord != 1:
        if Actual != Wanted:
            raise ValueError(
                "saved chamfer display inventory differs from its live drivers"
            )
        return Dimensions
    ByName = {Value.name: Value for Value in Dimensions}
    if len(Dimensions) != len(Wanted) or ByName.keys() != set(Wanted):
        raise ValueError("saved angle chamfer has missing or duplicate display roles")
    Ordered = tuple(ByName[NameValue] for NameValue in Wanted)
    if tuple(Value.kind for Value in Ordered) != ("distance", "angle"):
        raise ValueError(
            "saved angle chamfer display kinds differ from its live drivers"
        )
    return Ordered
