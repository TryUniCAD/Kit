from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveEnd import (
    RevolveEnd,
)

# only nodes in the witnessed display chains may participate in cold angular geometry
KRevAngleTypes = frozenset(
    (
        "moDisplayAngularDim_c",
        "moFeatureDimHandle_c",
        "AngleDim_c",
        "moAngleParameter_c",
    )
)


# map inventory must match the actual angle references rather than an inferred count
def CheckRevAngles(NodesValue: tuple[ArchiveNode, ...], EndValue: RevolveEnd) -> None:
    OwnedNodes = {
        NodeValue
        for AngleValue in (EndValue.AlongValue, EndValue.AgainstValue)
        if AngleValue is not None
        for NodeValue in (
            AngleValue.DisplayValue,
            AngleValue.HandleValue,
            AngleValue.DimensionValue,
            AngleValue.ParameterValue,
        )
    }
    Allocated = tuple(
        NodeValue
        for NodeValue in NodesValue
        if NodeValue.ClassValue.NameValue in KRevAngleTypes
    )
    if len(Allocated) != len(OwnedNodes) or set(Allocated) != OwnedNodes:
        raise ValueError("cache free revolve has duplicate or detached angle owners")
