from interchange.document.Models.DocumentError import DocumentError
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.document.Validation.DocumentBoundary import GetDocument
from interchange.Features.Offsets.FaceOffset import FaceOffset


# persisted omission markers cannot hide missing topology in an unfiltered source document
def CheckOffsetRead(SourceValue: object) -> None:
    Document = GetDocument(SourceValue)
    if Document is None:
        raise TypeError("offset input validation requires a cad document")
    for PartValue in WalkDocuments(Document):
        if PartValue.brep is None and any(
            isinstance(Feature.definition, FaceOffset)
            for Feature in PartValue.feature_timeline
        ):
            raise DocumentError("face offset input requires resolved face topology")
