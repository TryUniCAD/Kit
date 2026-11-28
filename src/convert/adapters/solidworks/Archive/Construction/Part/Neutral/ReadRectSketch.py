from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from interchange.geometry.Models.Sketch import Sketch


# the existing rectangle constructor must continue to require four axis aligned lines in one admitted closed loop
def ReadRectSketch(
    SketchValue: Sketch, UnitScale: float
) -> tuple[tuple[float, float], ...]:
    if len(SketchValue.entities) != 4:
        raise ValueError("plain boss requires one explicit four segment closed profile")
    VerticesValue = ReadLineLoop(SketchValue, UnitScale)
    if (
        len({PointValue[0] for PointValue in VerticesValue}) != 2
        or len({PointValue[1] for PointValue in VerticesValue}) != 2
    ):
        raise ValueError(
            "first plain boss profile requires a local axis aligned rectangle"
        )
    return PolygonInput(VerticesValue, 19000).VerticesValue
