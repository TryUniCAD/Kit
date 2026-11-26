from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingLine import (
    MakeRingLine,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequireProfile import (
    RequireProfile,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.WireRingMut import (
    WireRingMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# one immutable ring plan must generate all ordinary geometry identities indices and counters without saved programs
def MakePolygon(InputValue: PolygonInput, ProfileValue: ArchiveNode) -> PolygonGraph:
    if type(CastValue(object, InputValue)) is not PolygonInput:
        raise TypeError("polygon construction requires a validated polygon input")
    RequireProfile(ProfileValue)
    SketchValue = MakeSketchSeed(ProfileValue)
    PointValues = tuple(
        MakeRingPoint(SketchValue, PointValue, IndexValue)
        for IndexValue, PointValue in enumerate(InputValue.VerticesValue)
    )
    LineValues = tuple(
        MakeRingLine(SketchValue, PointValues, IndexValue)
        for IndexValue in range(len(PointValues))
    )
    WireRingMut(SketchValue, PointValues, LineValues)
    FieldsValue = SketchValue.FieldsValue
    FieldsValue["points"] = tuple(
        {"kind": 0, "point": PointValue.FieldsValue} for PointValue in PointValues
    )
    FieldsValue["lines"] = tuple(
        {"flags": 0, "line": LineValue.FieldsValue} for LineValue in LineValues
    )
    FieldsValue["npoints"], FieldsValue["nlines"] = len(PointValues), len(LineValues)
    FieldsValue["f130"], FieldsValue["f56c"] = len(LineValues) + 1, len(LineValues) + 1
    CreationValue = CastValue(dict[str, int], FieldsValue["f140"])
    CreationValue["f08"], CreationValue["f0c"] = (
        len(PointValues) + 1,
        len(LineValues) + 1,
    )
    return PolygonGraph(SketchValue, PointValues, LineValues)
