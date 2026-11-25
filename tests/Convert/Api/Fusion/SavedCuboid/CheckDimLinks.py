from pytest import approx as NearValue

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase


# saved size drivers must retain native ownership expression links and measured parameter values
def CheckDimLinks(
    Graph: NativeGraph, Document: CadDocument, CaseValue: SavedCase
) -> None:
    SketchValue = Document.sketches[0]
    Relations = SketchValue.constraints
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
