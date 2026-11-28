from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments

# the source namespace keeps stored part appearance distinct from portable material assignments
KPartLookKey = "solidworks.part_visual"


# native writers must refuse appearance evidence until effective ownership and transfer are verified
def CheckPartLook(Document: CadDocument) -> None:
    if any(KPartLookKey in Value.metadata for Value in WalkDocuments(Document)):
        raise ValueError(
            "native publication does not support stored SOLIDWORKS part appearance"
        )
