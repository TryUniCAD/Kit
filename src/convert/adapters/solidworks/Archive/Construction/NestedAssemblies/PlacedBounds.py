from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.JoinBoxes import (
    JoinBoxes,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlaceBox import (
    PlaceBox,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)


# parent bounds must fold transformed child local boxes with their native independent spheres instead of rebuilding a sphere from aggregate extrema
def PlacedBounds(Placements: tuple[TargetPlacement, ...]) -> dict[str, float]:
    ResultValue: dict[str, float] | None = None
    for ItemValue in Placements:
        BoxValue = PlaceBox(
            dict(ItemValue.TargetValue.BoundsValue),
            ItemValue.OccurrenceValue.FrameValue,
        )
        ResultValue = (
            BoxValue if ResultValue is None else JoinBoxes(ResultValue, BoxValue)
        )
    if ResultValue is None:
        raise ValueError("populated generated assembly bounds require a placement")
    return ResultValue
