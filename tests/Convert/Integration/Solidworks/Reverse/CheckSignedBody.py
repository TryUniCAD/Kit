from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Solidworks.Reverse.ReverseCase import ReverseCase


# signed analytic expectations constrain the complete returned solid rather than merely its feature flag
def CheckSignedBody(Document: CadDocument, Sample: ReverseCase) -> None:
    (BodyValue,) = Document.bodies
    Topology = BodyValue.topology
    assert (
        Document.brep is not None and Topology.solid_count == Topology.shell_count == 1
    )
    CornerCount = Sample.CornerCount
    assert (Topology.face_count, Topology.edge_count, Topology.vertex_count) == (
        CornerCount + 2,
        3 * CornerCount,
        2 * CornerCount,
    )
    assert Topology.volume is not None
    assert IsClose(Topology.volume, Sample.VolumeMm, rel_tol=1e-12)
    Centroid = CastValue(
        tuple[float, ...], BodyValue.attributes["solidworks.body_centroid_mm"]
    )
    assert all(
        IsClose(Value, Expected, abs_tol=1e-10)
        for Value, Expected in zip(Centroid, Sample.Centroid, strict=True)
    )
    Bounds = Topology.bounding_box
    assert Bounds is not None
    assert (Bounds.minimum.z, Bounds.maximum.z) == (
        (-Sample.DepthMm, 0.0) if Sample.IsReversed else (0.0, Sample.DepthMm)
    )
