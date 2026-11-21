from dataclasses import replace as ReplaceValue

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.document.Models.DocumentModel import CadDocument


# the exact cache free prism creator has no prior solid for the native boss family to join
def BindPrismCreate(Document: CadDocument, CreatorValue: FeatureStep) -> CadDocument:
    if (
        CreatorValue.kind != FeatureKind.KExtrusion
        or type(CreatorValue.definition) is not ExtrudeFeature
        or CreatorValue.operation != BooleanOp.KJoin
    ):
        return Document
    return ReplaceValue(
        Document,
        feature_timeline=tuple(
            (
                ReplaceValue(FeatureValue, operation=BooleanOp.KCreate)
                if FeatureValue is CreatorValue
                else FeatureValue
            )
            for FeatureValue in Document.feature_timeline
        ),
    )
