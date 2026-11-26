from pytest import approx as NearValue

from interchange.document.Models.DocumentModel import CadDocument


# independent cuboid calculations prevent matching writer and reader assumptions from hiding incorrect geometry
def VerifyGeometry(
    Document: CadDocument, Dimensions: tuple[float, float, float]
) -> None:
    WidthMm, DepthMm, ExpectedHeight = Dimensions
    assert len(Document.bodies) == 1 and Document.brep is not None
    Topology = Document.bodies[0].topology
    assert (
        Topology.solid_count,
        Topology.face_count,
        Topology.edge_count,
        Topology.vertex_count,
    ) == (1, 6, 12, 8)
    assert Topology.volume == NearValue(
        WidthMm * DepthMm * ExpectedHeight, rel=1e-10, abs=1e-8
    )
    Corners = sorted(
        (XCoord, YCoord, ZCoord)
        for XCoord in (0.0, WidthMm)
        for YCoord in (0.0, DepthMm)
        for ZCoord in (0.0, ExpectedHeight)
    )
    Vertices = sorted(
        (Vertex.point.x, Vertex.point.y, Vertex.point.z)
        for Vertex in Document.brep.vertices
    )
    for Observed, Expected in zip(Vertices, Corners, strict=True):
        assert Observed == NearValue(Expected, rel=1e-10, abs=1e-8)
