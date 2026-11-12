from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.CheckGridCage import (
    CheckGridCage,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridBounds import (
    GridBounds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridKnots import (
    GridKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridPatches import (
    GridPatches,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceGrips import (
    PlaceGrips,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceVertices import (
    PlaceVertices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.SpokeIndices import (
    SpokeIndices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def ConvertGrid(Surface: TsplineSurface) -> GridResult:
    CheckSurface(Surface)
    Mapping = CheckGridCage(Surface)
    Spokes = SpokeIndices(Surface.Topology)
    Places = PlaceVertices(Surface.Topology, Spokes)
    Width, Height, Order = PlaceGrips(Mapping, Places, len(Surface.Grips))
    Grips = tuple(Surface.Grips[Index] for Index in Order)
    Points = tuple((Grip.CoordX, Grip.CoordY, Grip.CoordZ) for Grip in Grips)
    Result = NubsSurface(
        3, 3, 0, 0, 0, 0, GridKnots(Width - 3), GridKnots(Height - 3), Points
    )
    Corners = (Points[0], Points[Width - 1], Points[-1], Points[-Width])
    return GridResult(
        Result,
        GridPatches(Surface.Topology, Spokes, Places),
        GridBounds(Result, Width, Height),
        Corners,
    )
