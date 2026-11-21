from pathlib import Path as FilePath

import pytest as PytestLib

from convert import open_document as OpenDocument
from interchange import Vector3 as SpaceVector

# committed vendor sources expose nonidentity supports independently of the research writer
KDisclosedParts = (
    FilePath(__file__).resolve().parents[5] / "re/solidworks/v2026/corpus/curves-discovery"
)


# authored top and right sketches must keep their distinct native support identities
@PytestLib.mark.parametrize(
    ("CaseName", "PlaneId", "Normal"),
    (
        ("D17TopCircle", 3, SpaceVector(0.0, 1.0, 0.0)),
        ("D18RightCircle", 4, SpaceVector(1.0, 0.0, 0.0)),
    ),
)
def TestPlaneOwners(CaseName: str, PlaneId: int, Normal: SpaceVector) -> None:
    Document = OpenDocument(
        KDisclosedParts / f"{CaseName}.SLDPRT",
        include_brep=False,
        include_tessellation=False,
    )
    assert Document.validate() == ()
    assert len(Document.sketches) == 1
    Sketch = Document.sketches[0]
    assert Sketch.id == "sldprt:sketch:26"
    assert Sketch.support_plane_id == f"sldprt:plane:{PlaneId}"
    assert Sketch.attributes["support_plane_source"] == "plane-reference"
    Plane = next(Plane for Plane in Document.support_planes if Plane.id == Sketch.support_plane_id)
    assert Plane.attributes["principal"] is True
    assert Plane.transform.z_axis == Normal
