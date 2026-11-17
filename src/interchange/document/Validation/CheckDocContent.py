from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.CheckDrawing import CheckDrawing


# drawings and design documents have different minimum useful content
def CheckDocContent(DocumentValue: CadDocument) -> tuple[str, ...]:
    if DocumentValue.DrawingValue is not None:
        Errors = CheckDrawing(DocumentValue.DrawingValue)
        if DocumentValue.assembly is not None:
            return (*Errors, "document cannot contain both a drawing and an assembly")
        return Errors
    Errors = ()
    if not DocumentValue.configurations:
        Errors = ("document has no configuration",)
    if (
        not DocumentValue.feature_timeline
        and not DocumentValue.parameters
        and DocumentValue.brep is None
        and not DocumentValue.brep_payloads
        and not DocumentValue.meshes
        and DocumentValue.assembly is None
    ):
        return (
            *Errors,
            "document has neither parameters, feature history, B-rep, mesh, nor assembly data",
        )
    return Errors
