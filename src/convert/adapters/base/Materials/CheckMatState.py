from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments


# native publication cannot discard an unresolved physical or visual assignment
def CheckMatState(Document: CadDocument) -> None:
    if any(
        any(Material.ColorValue is None for Material in PartValue.materials)
        or any(
            NoticeValue.code
            in (
                "sldprt.material_assignment_unresolved",
                "sldprt.material_domains_unresolved",
            )
            for NoticeValue in PartValue.diagnostics
        )
        for PartValue in WalkDocuments(Document)
    ):
        raise ValueError("unresolved material assignments cannot be exported")
