from interchange.document.Models.DocumentModel import CadDocument


# the fallback must not intercept a part with actual modeling features or drawings
def HasBareBrep(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.brep is not None
        and not DocumentValue.feature_timeline
        and DocumentValue.assembly is None
    )
