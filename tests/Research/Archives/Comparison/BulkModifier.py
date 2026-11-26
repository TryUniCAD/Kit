from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# live modifying histories must preserve the producer and terminal body ownership together
def BindModifier(
    Document: CadDocument,
    Feature: FeatureStep,
    Controls: tuple[Parameter, ...],
    Selections: tuple[Selection, ...] = (),
) -> CadDocument:
    Stock = ChangeRecord(
        Document.feature_timeline[-1],
        OutputBodyIds=tuple(BodyValue.id for BodyValue in Document.bodies),
    )
    return ChangeRecord(
        Document,
        parameters=(*Document.parameters, *Controls),
        selections=Selections,
        feature_timeline=(*Document.feature_timeline[:-1], Stock, Feature),
        bodies=tuple(
            (
                ChangeRecord(BodyValue, final_feature_id=Feature.id)
                if BodyValue.id in Feature.OutputBodyIds
                else BodyValue
            )
            for BodyValue in Document.bodies
        ),
    )
