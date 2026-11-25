from collections import Counter

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
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
    FixedPoints = tuple(
        Value
        for Value in Graph.ByClass("Point3D")
        if Value.Fields["isFixed"] and not Value.Fields["isOrigin"]
    )
    assert len(FixedPoints) == 1
    Entities = {Value.id: Value for Value in SketchValue.entities}
    assert Entities[FixedPoints[0].Identity].fixed is True
    assert Entities[FixedPoints[0].Identity].construction is False
    Origins = tuple(
        Value for Value in Graph.ByClass("Point3D") if Value.Fields["isOrigin"]
    )
    assert len(Origins) == 1 and Origins[0].Identity != FixedPoints[0].Identity
    assert Entities[Origins[0].Identity].fixed is True
    assert Entities[Origins[0].Identity].construction is True
    Parameters = {Value.id: Value for Value in Document.parameters}
    assert set(Parameters) == {Value.Identity for Value in Graph.ByClass("Parameter")}
    ByName = {Value.name: Value for Value in Parameters.values()}
    assert ByName["kitWidth"].value.value == NearValue(CaseValue.WidthMm)
    assert ByName["kitDepth"].value.value == NearValue(CaseValue.DepthMm)
    assert ByName["kitHeight"].value.value == NearValue(CaseValue.HeightMm)
    Dimensions = tuple(Value for Value in Relations if Value.parameter_id)
    assert {Value.id for Value in Dimensions} == {
        Value.Identity for Value in Graph.ByClass("FusionSketchLinearDim")
    }
    assert {Value.parameter_id for Value in Dimensions} == set(
        SketchValue.parameter_ids
    )
    Dependencies: set[str] = set()
    for Relation in Dimensions:
        assert Relation.parameter_id is not None
        Parameter = Parameters[Relation.parameter_id]
        assert Parameter.owner_id == Document.feature_timeline[0].id
        assert Parameter.expression is not None
        assert len(Parameter.expression.parameter_ids) == 1
        Dependencies.update(Parameter.expression.parameter_ids)
    assert Dependencies == {ByName["kitWidth"].id, ByName["kitDepth"].id}
