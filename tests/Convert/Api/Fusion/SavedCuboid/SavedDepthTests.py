from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import approx as NearValue

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument


# an existing native dimension edited archive proves stale extension placement can retain the old depth
def TestSavedDepth() -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/LocalOracle/DimensionAuthoring/vendor_DimensionedCuboidEdited.f3d"
    )
    Payload = Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == (
        "e74dd6e3bed9bc425c9387f8648fd115cce64e7910017e2956f47875c1ca2015"
    )
    Model = ReadDocument(Payload)
    Depth = next(
        Value
        for Value in BuildGraph(Model).ByClass("FusionSketchLinearDim")
        if Value.Fields["constraintType"] == 1 << 23
    )
    InfoValue = ObjectFields(Depth.Fields["LinearDimensionInfo"])
    assert PointCoords(InfoValue["startPoint"]) == NearValue((0.0, 2.9, 0.0))
    assert PointCoords(InfoValue["extnStartPoint"]) == NearValue((0.0, 2.3, 0.0))
    Document = OpenDocument(Payload, source_format="f3d")
    Parameters = {Value.name: Value.value.value for Value in Document.parameters}
    assert Parameters["boxWidth"] == NearValue(19.0)
    assert Parameters["boxDepth"] == NearValue(29.0)
    assert Parameters["boxHeight"] == NearValue(37.0)
    assert Document.bodies[0].topology.volume == NearValue(20387.0)
    assert Document.metadata["fusion.read_only"] is True
    Loaded = CadDocument.from_json(Document.to_json())
    assert Loaded == Document
    assert CheckContract(Loaded.metadata["fusion.native_state"], "model", 2) == Model
