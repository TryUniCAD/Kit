from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Distance.DistanceCut import DistanceCut
from tests.Research.Archives.Comparison.BulkTypedDocuments import (
    MakeCutDoc,
    MakeOutputDoc,
)


# ordered body operands need two unchanged anchored bodies so replacement checks cannot conceal ordering regressions
def MakeOrderDocs(Family: str) -> tuple[CadDocument, CadDocument]:
    Document = (
        MakeOutputDoc("ordered")
        if Family == "outputs"
        else MakeCutDoc("ordered", "same")
    )
    Feature = Document.feature_timeline[-1]
    BodyIds = tuple(BodyValue.id for BodyValue in Document.bodies)
    Definition = Feature.definition
    if isinstance(Definition, DistanceCut):
        Feature = ChangeRecord(
            Feature, definition=ChangeRecord(Definition, TargetBodyIds=BodyIds)
        )
    Feature = ChangeRecord(Feature, OutputBodyIds=BodyIds)
    Document = ChangeRecord(
        Document,
        feature_timeline=(*Document.feature_timeline[:-1], Feature),
        bodies=tuple(
            ChangeRecord(BodyValue, final_feature_id=Feature.id)
            for BodyValue in Document.bodies
        ),
    )
    ReversedIds = tuple(reversed(BodyIds))
    if Family == "cut_targets":
        assert isinstance(Feature.definition, DistanceCut)
        Changed = ChangeRecord(
            Feature,
            definition=ChangeRecord(Feature.definition, TargetBodyIds=ReversedIds),
        )
    else:
        Changed = ChangeRecord(Feature, OutputBodyIds=ReversedIds)
    return Document, ChangeRecord(
        Document, feature_timeline=(*Document.feature_timeline[:-1], Changed)
    )
