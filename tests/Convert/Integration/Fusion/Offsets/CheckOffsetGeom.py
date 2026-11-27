from math import isclose as IsClose
from typing import cast as CastValue
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from tests.Convert.Integration.Fusion.Offsets.OffsetCase import OffsetCase


# measured source solids must match complete public geometry after each saved driver edit
def CheckOffsetGeom(Document: CadDocument, Sample: OffsetCase) -> None:
    Reading = Sample.Reading
    Topology = Document.bodies[0].topology
    assert Topology.valid and Topology.solid_count == 1
    assert Topology.volume is not None and Topology.surface_area is not None
    assert IsClose(
        Topology.volume, CastValue(float, Reading["volume_cm3"]) * 1000, rel_tol=1e-9
    )
    assert IsClose(
        Topology.surface_area, CastValue(float, Reading["area_cm2"]) * 100, rel_tol=1e-9
    )
    Bounds = CastValue(list[list[float]], Reading["bounds_cm"])
    assert Topology.bounding_box is not None
    for Point, ExpectedPoint in zip(
        (Topology.bounding_box.minimum, Topology.bounding_box.maximum),
        Bounds,
        strict=True,
    ):
        assert all(
            IsClose(Actual, Wanted * 10, abs_tol=1e-8)
            for Actual, Wanted in zip(
                (Point.x, Point.y, Point.z), ExpectedPoint, strict=True
            )
        )
    Circle = Document.sketches[0].entities[-1].geometry
    assert isinstance(Circle, CircleGeometry)
    Profile = CastValue(dict[str, object], Reading["profile"])
    assert IsClose(
        Circle.radius, CastValue(float, Profile["radius_cm"]) * 10, abs_tol=1e-9
    )
    assert (
        Document.brep is not None
        and not Document.brep_payloads
        and not Document.diagnostics
    )
