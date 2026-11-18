from math import isclose as IsClose, pi as PiValue
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from tests.Convert.Solidworks.Research.Cut.MakePocketArchive import MakePocketArchive


# the public default read must recover a closed analytic cavity while leaving the driving cut history editable
def TestCacheFreePocketRead(TmpPath: FilePath) -> None:
    Payload = MakePocketArchive(TmpPath / "Inputs")
    Document = OpenDoc(Payload, source_format="solidworks.sldprt")
    assert not Document.validate() and Document.brep_payloads == ()
    Brep = Document.brep
    (BodyValue,) = Document.bodies
    assert Brep is not None and not Brep.validate(frozenset((BodyValue.id,)))
    assert (len(Brep.faces), len(Brep.edges), len(Brep.vertices)) == (8, 14, 10)
    assert sorted(len(Face.loop_ids) for Face in Brep.faces) == [1] * 6 + [2, 2]
    Topology = BodyValue.topology
    assert Topology is not None and Topology.solid_count == 1
    assert Topology.volume is not None and Topology.surface_area is not None
    Width, Height, Depth, Radius, CutDepth = 61.7, 37.9, 14.3, 4.1, 3.8
    Volume = Width * Height * Depth - PiValue * Radius**2 * CutDepth
    Area = 2 * (Width * Height + (Width + Height) * Depth + PiValue * Radius * CutDepth)
    assert IsClose(Topology.volume, Volume, rel_tol=1e-12)
    assert IsClose(Topology.surface_area, Area, rel_tol=1e-12)
    (Cut,) = tuple(
        Feature
        for Feature in Document.feature_timeline
        if str(Feature.operation) == "cut"
    )
    assert BodyValue.final_feature_id == Cut.id
    (Sketch,) = tuple(
        Sketch for Sketch in Document.sketches if Sketch.id == Cut.sketch_id
    )
    assert Sketch.constraints == ()
