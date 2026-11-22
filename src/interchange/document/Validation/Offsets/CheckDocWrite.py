from interchange.document.Models.DocumentError import DocumentError
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.document.Validation.DocumentBoundary import GetDocument
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.Features.Distance.DistanceCut import DistanceCut


# public document files cannot masquerade as evaluated outputs for inspection only native histories
def CheckDocWrite(SourceValue: object) -> None:
    Document = GetDocument(SourceValue)
    if Document is None:
        raise TypeError("document file persistence requires a cad document")
    for PartValue in WalkDocuments(Document):
        if PartValue.metadata.get("fusion.read_only") is True or any(
            isinstance(Feature.definition, (FaceOffset, DistanceCut))
            for Feature in PartValue.feature_timeline
        ):
            raise DocumentError(
                "inspection-only histories cannot be written with write_json; use kit decode for inspection output"
            )
