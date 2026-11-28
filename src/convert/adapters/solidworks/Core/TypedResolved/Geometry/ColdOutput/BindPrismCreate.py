from dataclasses import replace as ReplaceValue

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.document.Models.DocumentModel import CadDocument


# the exact cache free prism creator has no prior solid for the native boss family to join
def BindPrismCreate(
    Document: CadDocument, CreatorValue: FeatureStep, *, FirstScope: bool = False
) -> CadDocument:
    Definition = CreatorValue.definition
    if (
        CreatorValue.kind != FeatureKind.KExtrusion
        or type(Definition) is not ExtrudeFeature
        or CreatorValue.operation != BooleanOp.KJoin
    ):
        if FirstScope:
            raise ValueError(
                "cache free first creator lost its neutral extrusion owner"
            )
        return Document
    Bound = (
        ScopedExtrude(Definition, "first_creator", (), ()) if FirstScope else Definition
    )
    return ReplaceValue(
        Document,
        feature_timeline=tuple(
            (
                ReplaceValue(
                    FeatureValue, operation=BooleanOp.KCreate, definition=Bound
                )
                if FeatureValue is CreatorValue
                else FeatureValue
            )
            for FeatureValue in Document.feature_timeline
        ),
    )
