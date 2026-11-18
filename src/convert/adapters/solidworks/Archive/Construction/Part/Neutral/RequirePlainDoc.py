from typing import cast as CastValue
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid


# the first candidate must reject unsupported neutral domains rather than silently omit authored data from a superficially valid part
def RequirePlainDoc(DocumentValue: CadDocument) -> None:
    CheckPartScope(DocumentValue, (1,))


# all ordinary boss profiles enforce common document loss guards before consulting their own driving parameter owners
def CheckPartScope(
    DocumentValue: CadDocument,
    ParameterCounts: tuple[int, ...],
    HistoryCount: int = 1,
) -> None:
    if not isinstance(CastValue(object, DocumentValue), CadDocument):
        raise TypeError("plain boss candidate requires a real neutral cad document")
    AssertValid(DocumentValue)
    if (
        DocumentValue.assembly is not None
        or DocumentValue.DrawingValue is not None
        or DocumentValue.brep is not None
    ):
        raise ValueError(
            "plain boss candidate does not admit assemblies drawings or native boundary payloads"
        )
    if (
        DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.materials
        or DocumentValue.selections
    ):
        raise ValueError(
            "plain boss candidate does not admit extra mesh payload material or selection semantics"
        )
    if (
        len(DocumentValue.configurations),
        len(DocumentValue.support_planes),
        len(DocumentValue.sketches),
        len(DocumentValue.feature_timeline),
        len(DocumentValue.bodies),
    ) != (1, 1, HistoryCount, HistoryCount, 1) or len(
        DocumentValue.parameters
    ) not in ParameterCounts:
        raise ValueError(
            "plain boss candidate requires one configuration length support sketch operation and body"
        )
    if set(DocumentValue.metadata) - {"name"}:
        raise ValueError(
            "plain boss candidate does not admit unprojected document metadata"
        )
