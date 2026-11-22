from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.Geometry.Extrude.Polygon.DraftMass import DraftMass


# volume area centroid and the complete inertia tensor must share the same drafted dimensions
def CheckDraftMass(Context: ExtrudeContext, Measures: DraftMass) -> None:
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    SameNumbers(
        (NumberValue(Cache["volume"]), NumberValue(Cache["area"])),
        (Measures.Volume / 1000, Measures.Area / 100),
    )
    SameNumbers(
        PointCoords(Cache["cog"]), tuple(Value / 10 for Value in Measures.Center)
    )
    SameNumbers(
        PointCoords(Cache["moi"]), tuple(Value / 100000 for Value in Measures.Inertia)
    )
    SameNumbers(
        PointCoords(Cache["moiOffDiag"]),
        tuple(Value / 100000 for Value in Measures.CrossTerms),
    )
