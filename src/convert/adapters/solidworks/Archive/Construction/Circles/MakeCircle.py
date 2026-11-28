from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import (
    MakeArcHandle,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleArc import (
    MakeCircleArc,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequireProfile import (
    RequireProfile,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# one circle allocates centre and seam by permanence order while storing their independent point array order
def MakeCircle(InputValue: CircleInput, ProfileValue: ArchiveNode) -> CircleGraph:
    if type(CastValue(object, InputValue)) is not CircleInput:
        raise TypeError("ordinary circle construction requires a validated circle")
    RequireProfile(ProfileValue)
    SketchValue = MakeSketchSeed(ProfileValue)
    MarkerValue = MakeRingPoint(SketchValue, InputValue.MarkerValue, 0)
    CenterValue = MakeRingPoint(SketchValue, InputValue.CenterValue, 1)
    PointValues = (CenterValue, MarkerValue)
    ArcValue = MakeCircleArc(SketchValue, CenterValue, MarkerValue, 0, 1, 0)
    MarkerValue.FieldsValue.update(
        {"fe4": 2, "fe8": 2, "h1": MakeArcHandle(SketchValue, ArcValue, 0)}
    )
    CenterValue.FieldsValue.update({"fe8": 1, "fec": 1})
    ArcValues = (ArcValue,)
    FieldsValue = SketchValue.FieldsValue
    FieldsValue.update(
        {
            "points": tuple(
                {"kind": 0, "point": PointValue.FieldsValue}
                for PointValue in PointValues
            ),
            "arcs": tuple(
                {"flags": 0, "arc": EntryValue.FieldsValue} for EntryValue in ArcValues
            ),
            "npoints": len(PointValues),
            "narcs": len(ArcValues),
            "f130": len(ArcValues) + 1,
            "f56c": len(ArcValues) + 1,
        }
    )
    CreationValue = CastValue(dict[str, int], FieldsValue["f140"])
    CreationValue["f08"] = len(PointValues) + 1
    CreationValue["f10"] = len(ArcValues) + 1
    return CircleGraph(SketchValue, ArcValue, CenterValue, MarkerValue)
