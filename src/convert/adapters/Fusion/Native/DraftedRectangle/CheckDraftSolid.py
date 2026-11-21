from convert.adapters.Fusion.Native.DraftedRectangle.MatchDraftPoints import (
    MatchDraftPoints,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Geometry.Extrude.Polygon.DraftMass import DraftMass
from interchange.brep.Topology.BrepModel import BrepModel


# every saved vertex and outward face must belong to the independently generated drafted solid
def CheckDraftSolid(
    Shell: PlanarShell, Geometry: BrepModel, Measures: DraftMass
) -> tuple[int, ...]:
    if (
        Shell.Placement is not None
        or len(Shell.VertexRefs) != 8
        or len(Shell.FaceRefs) != 6
        or any(len(Ring) != 4 for Ring in Shell.Rings)
    ):
        raise ValueError(
            "Native drafted rectangle requires one untransformed six face solid"
        )
    Points = tuple(
        (Vertex.point.x / 10, Vertex.point.y / 10, Vertex.point.z / 10)
        for Vertex in Geometry.vertices
    )
    Indices = MatchDraftPoints(Shell.PointsCm, Points)
    ExpectedFaces = {
        frozenset(range(4)),
        frozenset(range(4, 8)),
        *(
            frozenset((Index, (Index + 1) % 4, Index + 4, (Index + 1) % 4 + 4))
            for Index in range(4)
        ),
    }
    if {
        frozenset(Indices[Index] for Index in Ring) for Ring in Shell.Rings
    } != ExpectedFaces:
        raise ValueError(
            "Native drafted rectangle faces disagree with its generated caps and walls"
        )
    SameNumbers((Shell.VolumeCm3,), (Measures.Volume / 1000,))
    return Indices
