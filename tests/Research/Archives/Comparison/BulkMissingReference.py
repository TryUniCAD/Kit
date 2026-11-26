from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.Offsets.FaceOffset import FaceOffset


# dangling typed operands must reach document admission instead of silently becoming comparison edges
def LoseTypedRef(Document: CadDocument, RoleName: str) -> CadDocument:
    Feature = Document.feature_timeline[-1]
    if RoleName == "OutputBodyIds":
        Feature = ChangeRecord(Feature, OutputBodyIds=("missing",))
    elif isinstance(Feature.definition, DistanceCut):
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(Feature.definition, TargetBodyIds=("missing",)),
        )
    else:
        assert isinstance(Feature.definition, FaceOffset)
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(Feature.definition, **{RoleName: "missing"}),
        )
    return ChangeRecord(
        Document, feature_timeline=(*Document.feature_timeline[:-1], Feature)
    )
