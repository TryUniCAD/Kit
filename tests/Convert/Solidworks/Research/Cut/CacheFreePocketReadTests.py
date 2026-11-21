from math import isclose as IsClose, pi as PiValue
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from tests.Convert.Solidworks.Research.Cut.MakePocketArchive import MakePocketFile


# the public default read must recover a closed analytic cavity while leaving the driving cut history editable
def TestPocketRead(TmpPath: FilePath) -> None:
    Payload = MakePocketFile(TmpPath / "Inputs")
    Document = OpenDoc(Payload, source_format="solidworks.sldprt")
    assert not Document.validate() and Document.brep_payloads == ()
    ModelBrep = Document.brep
    (BodyValue,) = Document.bodies
    assert ModelBrep is not None and not ModelBrep.validate(frozenset((BodyValue.id,)))
    assert (len(ModelBrep.faces), len(ModelBrep.edges), len(ModelBrep.vertices)) == (
        8,
        14,
        10,
    )
    assert sorted(len(FaceValue.loop_ids) for FaceValue in ModelBrep.faces) == [
        1
    ] * 6 + [2, 2]
    Topology = BodyValue.topology
    assert Topology.solid_count == 1
    assert Topology.volume is not None and Topology.surface_area is not None
    Width, Height, Depth, Radius, CutDepth = 61.7, 37.9, 14.3, 4.1, 3.8
    Volume = Width * Height * Depth - PiValue * Radius**2 * CutDepth
    AreaValue = 2 * (
        Width * Height + (Width + Height) * Depth + PiValue * Radius * CutDepth
    )
    assert IsClose(Topology.volume, Volume, rel_tol=1e-12)
    assert IsClose(Topology.surface_area, AreaValue, rel_tol=1e-12)
    (CutFeature,) = tuple(
        Feature
        for Feature in Document.feature_timeline
        if str(Feature.operation) == "cut"
    )
    assert BodyValue.final_feature_id == CutFeature.id
    (Sketch,) = tuple(
        Sketch for Sketch in Document.sketches if Sketch.id == CutFeature.sketch_id
    )
    assert Sketch.constraints == ()
