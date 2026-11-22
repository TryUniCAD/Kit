from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    KEllipStations,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ProjectEllip import (
    EvalEllipGeo,
)
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.Sketch import SketchEntity


# each physical station requires the exact pair of finite metre coordinates retained by the reader
def ReadStation(Value: object) -> tuple[float, float]:
    if type(Value) is not tuple:
        raise ValueError("SOLIDWORKS ellipse readback requires typed conic stations")
    First, Second = CastValue(tuple[object, ...], Value)
    return RequireScalar(First), RequireScalar(Second)


# the conic stations must reconstruct the actual public ellipse before they can bind a constructor plan
def ReadEllipPos(Entity: SketchEntity, Depth: float) -> KEllipStations:
    Geometry = Entity.geometry
    Values = Entity.attributes.get("native_ellipse_stations_m")
    if type(Geometry) is not EllipseGeometry or type(Values) is not tuple:
        raise ValueError("SOLIDWORKS ellipse readback requires exact conic geometry")
    Center, Major, Minor = CastValue(tuple[object, ...], Values)
    Stations = (ReadStation(Center), ReadStation(Major), ReadStation(Minor))
    if EvalEllipGeo(Stations, Depth) != Geometry:
        raise ValueError(
            "SOLIDWORKS ellipse readback conic differs from its typed stations"
        )
    return Stations
