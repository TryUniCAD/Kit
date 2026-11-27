from pytest import approx as ApproxValue

from interchange.brep.Surfaces.BrepSurfaces import (
    CylinderSurface,
    PlaneSurface,
    TorusSurface,
)
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.RimFillet.Public.RimApiState import RimApiState


# neutral topology and all recorded geometry measures must agree after complete source admission
def CheckRimMeasure(Document: CadDocument, Expected: RimApiState) -> None:
    (BodyValue,) = Document.bodies
    Counts = BodyValue.topology
    assert (
        Counts.solid_count,
        Counts.shell_count,
        Counts.face_count,
        Counts.edge_count,
        Counts.vertex_count,
    ) == (1, 1, 4, 3, 3)
    assert Counts.volume == ApproxValue(Expected.Volume, rel=1e-6, abs=1e-5)
    assert Counts.surface_area == ApproxValue(Expected.AreaValue, rel=1e-6, abs=1e-6)
    assert BodyValue.attributes["analytic_centroid_mm"] == ApproxValue(
        Expected.Center, rel=1e-6, abs=1e-7
    )
    assert Counts.bounding_box is not None
    Lower, Upper = Counts.bounding_box.minimum, Counts.bounding_box.maximum
    assert (Lower.x, Lower.y, Lower.z) == ApproxValue(
        Expected.Lower, rel=1e-6, abs=1e-7
    )
    assert (Upper.x, Upper.y, Upper.z) == ApproxValue(
        Expected.Upper, rel=1e-6, abs=1e-7
    )
    Geometry = Document.brep
    assert Geometry is not None and Geometry.validate(frozenset((BodyValue.id,))) == ()
    assert sum(isinstance(Value, TorusSurface) for Value in Geometry.surfaces) == 1
    assert sum(isinstance(Value, CylinderSurface) for Value in Geometry.surfaces) == 1
    assert sum(isinstance(Value, PlaneSurface) for Value in Geometry.surfaces) == 2
    assert len(Geometry.loops) == len(Geometry.coedges) == 6
