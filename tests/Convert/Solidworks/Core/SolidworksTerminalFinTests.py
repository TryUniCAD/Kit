from hashlib import sha256 as Fingerprint
from math import isclose as IsClose

from convert import open_document as OpenDocument
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector
from tests.Convert.Api.ApiTestPaths import KRootPath

# the disclosed ladder part has a measured current schema and positive native volume
KTerminalPart = KRootPath / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"

# the integrated read must use the same disclosed geometry as the orientation comparison
KTerminalDigest = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"


# a strict public read must return an outward closed shell for the native rectangular part
def TestFinWinding() -> None:
    SourceData = KTerminalPart.read_bytes()
    assert Fingerprint(SourceData).hexdigest() == KTerminalDigest
    Document = OpenDocument(
        SourceData,
        source_format="solidworks.sldprt",
        strict=True,
        include_brep=True,
        include_tessellation=False,
    )
    assert any(
        PayloadValue.schema == "SCH_3701250_37102_13006"
        for PayloadValue in Document.brep_payloads
    )
    ModelValue = Document.brep
    assert ModelValue is not None and not ModelValue.validate()
    assert (
        len(ModelValue.bodies),
        len(ModelValue.vertices),
        len(ModelValue.edges),
        len(ModelValue.faces),
        len(ModelValue.loops),
    ) == (1, 8, 12, 6, 6)
    (ShellValue,) = ModelValue.shells
    assert ShellValue.closed
    Vertices = {Vertex.id: Vertex.point for Vertex in ModelValue.vertices}
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in ModelValue.edges}
    StartPoints = {
        Coedge.id: Vertices[
            (
                Edges[Coedge.edge_id].end_vertex_id
                if Coedge.reversed
                else Edges[Coedge.edge_id].start_vertex_id
            )
        ]
        for Coedge in ModelValue.coedges
    }
    VolumeSum = 0.0
    for LoopValue in ModelValue.loops:
        First, Second, Third, Fourth = (
            StartPoints[UseId] for UseId in LoopValue.coedge_ids
        )
        VolumeSum += DotVector(First, CrossVector(Second, Third))
        VolumeSum += DotVector(First, CrossVector(Third, Fourth))
    assert IsClose(VolumeSum / 6.0, 8000.0, rel_tol=0.0, abs_tol=1e-9)
