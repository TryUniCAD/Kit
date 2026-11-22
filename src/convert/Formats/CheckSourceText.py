from convert.Formats.CheckPartText import CheckPartText
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments


# unavailable text remains a publication blocker on the root and every owned child
def CheckSourceText(DocumentValue: CadDocument) -> None:
    for PartValue in WalkDocuments(DocumentValue):
        CheckPartText(PartValue)
