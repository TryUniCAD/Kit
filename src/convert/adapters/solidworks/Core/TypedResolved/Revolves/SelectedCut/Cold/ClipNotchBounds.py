from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.MakeRevMerid import (
    MakeRevMeridian,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# the cutter overlaps only the common radial band and retains its signed axial extent
def ClipNotchBounds(
    Stock: RevolveOwner, Cutter: RevolveOwner
) -> tuple[float, float, float, float]:
    StockProfile = MakeRevMeridian(Stock)
    ToolProfile = MakeRevMeridian(Cutter)
    StockRadii = tuple(Radius for Radius, _ in StockProfile)
    ToolRadii = tuple(Radius for Radius, _ in ToolProfile)
    Orientation = -1 if Cutter.IsReverse else 1
    ToolHeights = tuple(Orientation * Height for _, Height in ToolProfile)
    Lower = max(min(StockRadii), min(ToolRadii))
    Upper = min(max(StockRadii), max(ToolRadii))
    return Lower, Upper, min(ToolHeights), max(ToolHeights)
