from dataclasses import replace as CopyData

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.PlainWriting.ReversePrep.PrepCase import PrepCase


# the neutral feature itself must request reversal before the ordinary preparation pipeline is entered
def MakePrepDoc(CaseValue: PrepCase) -> CadDocument:
    Document = MakePlainDoc(CaseValue.NameValue, CaseValue.Points, CaseValue.DepthMm)
    Feature = Document.feature_timeline[0]
    assert isinstance(Feature.definition, ExtrudeFeature)
    return CopyData(
        Document,
        feature_timeline=(
            CopyData(
                Feature,
                definition=CopyData(Feature.definition, reversed=CaseValue.IsReversed),
            ),
        ),
    )
