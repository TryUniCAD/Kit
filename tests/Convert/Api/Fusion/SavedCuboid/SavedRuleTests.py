from collections import Counter

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.SavedCuboid.CheckDimLinks import CheckDimLinks
from tests.Convert.Api.Fusion.SavedCuboid.CheckFixPoint import CheckFixPoint
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# projected solver intent must retain every measured rule and the actual fixed corner identity
@MarkTests.parametrize("CaseValue", KSavedCases)
def TestSavedRules(CaseValue: SavedCase) -> None:
    Payload = SavedSource(CaseValue).read_bytes()
    Graph = BuildGraph(ReadDocument(Payload))
    Document = OpenDocument(Payload, source_format="f3d")
    SketchValue = Document.sketches[0]
    Relations = SketchValue.constraints
    assert Counter(Value.kind for Value in Relations) == {
        "horizontal": 2,
        "vertical": 2,
        "distance_x": 1,
        "distance_y": 1,
    }
    assert all(Value.driving and not Value.suppressed for Value in Relations)
    NativeRules = Graph.ByClass("SketchGeomConstraint")
    AxisRules = tuple(
        Value for Value in Relations if Value.kind in ("horizontal", "vertical")
    )
    assert {Value.id for Value in AxisRules} == {
        Value.Identity for Value in NativeRules
    }
    CheckFixPoint(Graph, SketchValue)
    CheckDimLinks(Graph, Document, CaseValue)
