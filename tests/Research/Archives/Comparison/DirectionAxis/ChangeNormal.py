from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.VectorSpace import SpaceVector


# a wrong explicit normal must retain its actual feature and all other sketch bindings
def ChangeNormal(Document: CadDocument) -> CadDocument:
    (IndexValue,) = (
        IndexValue
        for IndexValue, Feature in enumerate(Document.feature_timeline)
        if Feature.id == "sldprt:feature:34"
    )
    BossValue = Document.feature_timeline[IndexValue]
    Definition = BossValue.definition
    assert isinstance(Definition, ExtrudeFeature)
    Changed = ChangeRecord(
        BossValue, definition=ChangeRecord(Definition, direction=SpaceVector(0, 1, 0))
    )
    Timeline = Document.feature_timeline
    return ChangeRecord(
        Document,
        feature_timeline=Timeline[:IndexValue]
        + (Changed,)
        + Timeline[IndexValue + 1 :],
    )
