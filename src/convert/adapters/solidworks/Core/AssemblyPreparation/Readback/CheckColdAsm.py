from interchange.document.Models.DocumentModel import CadDocument


# the reopened root may only expose the generated empty mate containers beside its exact history
def CheckColdAsm(Document: CadDocument) -> None:
    GraphValue = Document.assembly
    if (
        GraphValue is None
        or GraphValue.mates
        or GraphValue.mate_entities
        or GraphValue.mate_groups
        or Document.sketches
        or Document.parameters
        or Document.bodies
        or Document.meshes
        or Document.materials
        or Document.selections
        or Document.brep is not None
        or any(
            Payload.format_id != "solidworks.mates"
            or Payload.attributes.get("declared_count") != 0
            or Payload.attributes.get("records") != ()
            for Payload in Document.brep_payloads
        )
    ):
        raise ValueError(
            "reopened nested assembly has unsupported mates or model state"
        )
