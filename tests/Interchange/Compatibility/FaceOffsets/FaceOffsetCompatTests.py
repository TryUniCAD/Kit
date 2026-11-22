from dataclasses import replace as CopyData
import pytest as Pytest

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Offsets.GetOffsetValue import GetOffsetValue
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import SelectPathElem
from tests.Interchange.Compatibility.FaceOffsets.BuildOffsetDoc import BuildOffsetDoc


# public document serialization must validate the complete selected face and live parameter graph
def CheckOffsetDoc() -> None:
    Document = BuildOffsetDoc()
    Document.assert_valid()
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    Feature = Restored.feature_timeline[-1]
    assert isinstance(Feature.definition, FaceOffset)
    Parameters = {Value.id: Value for Value in Restored.parameters}
    Selections = {Value.id: Value for Value in Restored.selections}
    assert GetOffsetValue(Feature, Feature.definition, Parameters, Selections) == 0.0


# malformed wire graphs must fail public validation instead of silently losing offset intent
@Pytest.mark.parametrize("Failure", ("owner", "face", "producer"))
def CheckBadOffset(Failure: str) -> None:
    Document = BuildOffsetDoc()
    if Failure == "owner":
        Parameter = CopyData(Document.parameters[-1], owner_id="missing")
        Document = CopyData(Document, parameters=(*Document.parameters[:-1], Parameter))
    elif Failure == "face":
        Selected = Document.selections[0]
        Selected = CopyData(
            Selected, path=(Selected.path[0], SelectPathElem("face", "missing"))
        )
        Document = CopyData(Document, selections=(Selected,))
    else:
        Feature = CopyData(Document.feature_timeline[-1], input_feature_ids=())
        Document = CopyData(
            Document, feature_timeline=(*Document.feature_timeline[:-1], Feature)
        )
    with Pytest.raises(ValueError):
        CadDocument.from_json(Document.to_json()).assert_valid()
