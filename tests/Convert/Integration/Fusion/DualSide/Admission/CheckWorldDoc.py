from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# source placement must drive the public support and measured world bounds without a second body rotation
def CheckWorldDoc(Document: CadDocument, Sample: DualCase) -> None:
    (Support,) = Document.support_planes
    assert Support.transform == Sample.Frame and Support.name == "XZ"
    assert Document.sketches[0].support_plane_id == Support.id
    Bounds = Document.bodies[0].topology.bounding_box
    assert Bounds is not None
    for Actual, Expected in zip(
        (Bounds.minimum, Bounds.maximum),
        CastValue(list[list[float]], Sample.Reading["bounds_cm"]),
        strict=True,
    ):
        assert all(
            IsClose(Value, Wanted * 10, abs_tol=1e-7)
            for Value, Wanted in zip(
                (Actual.x, Actual.y, Actual.z), Expected, strict=True
            )
        )
