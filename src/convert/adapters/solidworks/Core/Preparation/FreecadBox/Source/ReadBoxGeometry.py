from itertools import product
from math import isclose

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument


# the independently derived box envelope can corroborate an optional source shape cache
def CheckBoxCache(
    Shape: BrepModel,
    Minimum: tuple[float, float, float],
    Maximum: tuple[float, float, float],
) -> None:
    Counts = (
        len(Shape.vertices),
        len(Shape.edges),
        len(Shape.faces),
        len(Shape.shells),
        len(Shape.bodies),
    )
    RequireBox(
        Counts == (8, 12, 6, 1, 1),
        "FreeCAD shape cache is inconsistent with an ordinary rectangular solid",
    )
    Points = tuple(
        (Vertex.point.x, Vertex.point.y, Vertex.point.z) for Vertex in Shape.vertices
    )
    Corners = product(*zip(Minimum, Maximum, strict=True))
    RequireBox(
        all(
            sum(
                all(
                    isclose(Actual, Target, rel_tol=0, abs_tol=1e-10)
                    for Actual, Target in zip(Point, Corner, strict=True)
                )
                for Point in Points
            )
            == 1
            for Corner in Corners
        ),
        "FreeCAD box cache is inconsistent with the independently computed origin and dimensions",
    )


# signed world bounds and mass properties follow the authored rigid plane attachment
def ReadBoxGeometry(
    DocumentValue: CadDocument, Sizes: tuple[float, float, float]
) -> dict[str, object]:
    Length, Width, Height = Sizes
    Minimum = (0.0, -Height, 0.0)
    Maximum = (Length, 0.0, Width)
    Shape = DocumentValue.brep
    if Shape is not None:
        CheckBoxCache(Shape, Minimum, Maximum)
    return {
        "body_count": 1,
        "volume_m3": Length * Width * Height * 1e-9,
        "area_m2": 2 * (Length * Width + Width * Height + Height * Length) * 1e-6,
        "centre_m": [
            (Lower + Upper) / 2000
            for Lower, Upper in zip(Minimum, Maximum, strict=True)
        ],
        "bounds_mm": [list(Minimum), list(Maximum)],
        "source_cache_compared": Shape is not None,
    }
