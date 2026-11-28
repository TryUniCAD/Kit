from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument


# an ordinary revolve constructor must reject extra neutral domains before any native output can be allocated
def RequireRevDoc(DocumentValue: CadDocument) -> None:
    if type(CastValue(object, DocumentValue)) is not CadDocument:
        raise TypeError("revolve construction requires a real neutral document")
    DocumentValue.assert_valid()
    if (
        DocumentValue.assembly is not None
        or DocumentValue.DrawingValue is not None
        or DocumentValue.brep is not None
        or DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.materials
        or DocumentValue.diagnostics
    ):
        raise ValueError("revolve construction does not admit other document domains")
    if tuple(
        map(
            len,
            (
                DocumentValue.configurations,
                DocumentValue.support_planes,
                DocumentValue.sketches,
                DocumentValue.feature_timeline,
                DocumentValue.bodies,
                DocumentValue.selections,
            ),
        )
    ) != (1, 1, 1, 1, 1, 1):
        raise ValueError("revolve construction requires one complete ordinary model")
    if set(DocumentValue.metadata) != {"name"} or DocumentValue.units != "mm":
        raise ValueError("revolve construction requires explicit names and millimetres")
