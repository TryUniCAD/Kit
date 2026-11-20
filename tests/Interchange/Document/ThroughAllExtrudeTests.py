from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from tests.Interchange.Document.DistanceExtrudeTests import BuildDistExt


# a complete portable cut history needs real geometric ends even where neither direction has a driving length
def TestThroughWire() -> None:
    Source = BuildDistExt()
    (Producer,) = Source.feature_timeline
    for SecondEnd in (None, ExtrudeEnd.KThroughAll):
        EndDefinition = ExtrudeFeature(
            end_condition=ExtrudeEnd.KThroughAll,
            reversed=SecondEnd is None,
            second_end_condition=SecondEnd,
        )
        CutFeature = FeatureStep(
            id="through-cut",
            name="Through Cut",
            kind=FeatureKind.KExtrusion,
            order=1,
            sketch_id=Producer.sketch_id,
            operation=BooleanOp.KCutOperation,
            definition=EndDefinition,
            input_feature_ids=(Producer.id,),
        )
        Document = ReplaceValue(Source, feature_timeline=(Producer, CutFeature))
        assert not Document.validate()
        Restored = CadDocument.from_json(Document.to_json())
        assert Restored == Document
        Bound = Restored.feature_timeline[1].definition
        assert isinstance(Bound, ExtrudeFeature)
        assert (
            Bound.length is None
            and Bound.Length is None
            and Bound.second_length is None
        )
        assert Bound.second_end_condition == SecondEnd
        assert Restored.feature_timeline[1].parameter_ids == ()
        with Raises(ValueError, match="requires a primary length"):
            _ = ReplaceValue(Bound, end_condition=ExtrudeEnd.KBlind)
