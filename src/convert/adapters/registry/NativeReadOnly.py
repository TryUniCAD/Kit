from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments


# inspection only source projections cannot become qualified exports through alternate writer apis
def CheckReadOnly(Document: CadDocument) -> None:
    SourcePaths = tuple(
        PartValue.source.path
        for PartValue in WalkDocuments(Document)
        if PartValue.metadata.get("fusion.read_only") is True
    )
    if SourcePaths:
        raise ValueError(
            "read-only Fusion histories cannot be exported: " + "; ".join(SourcePaths)
        )
