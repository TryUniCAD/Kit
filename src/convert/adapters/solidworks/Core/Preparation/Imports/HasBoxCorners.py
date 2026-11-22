from itertools import product as Cartesian

from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# the measured prism profile requires the exact eight corners of an axis aligned box
def HasBoxCorners(ModelValue: BrepModel) -> bool:
    if (
        len(ModelValue.faces) != 6
        or len(ModelValue.edges) != 12
        or len(ModelValue.vertices) != 8
        or any(type(Value) is not PlaneSurface for Value in ModelValue.surfaces)
        or any(type(Value) is not LineCurve for Value in ModelValue.curves)
    ):
        return False
    Corners = {
        (Value.point.x, Value.point.y, Value.point.z) for Value in ModelValue.vertices
    }
    Stations = tuple(set(AxisValue) for AxisValue in zip(*Corners, strict=True))
    return (
        len(Corners) == 8
        and all(len(AxisValue) == 2 for AxisValue in Stations)
        and Corners == set(Cartesian(*Stations))
    )
