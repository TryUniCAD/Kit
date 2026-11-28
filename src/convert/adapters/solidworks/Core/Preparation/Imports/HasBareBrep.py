from interchange.document.Models.DocumentModel import CadDocument


# the fallback cannot own parametric histories or assembly structures
def HasBareBrep(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.brep is not None
        and not DocumentValue.feature_timeline
        and DocumentValue.assembly is None
    )
