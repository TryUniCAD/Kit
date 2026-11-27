from typing import cast as CastValue
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# the first adapter candidate must reject unrepresented annotations provenance and topology instead of silently treating the supported shape as complete document admission
def CheckPlainScope(DocumentValue: CadDocument) -> None:
    if type(CastValue(object, DocumentValue)) is not CadDocument:
        raise TypeError("plain part preparation requires the concrete neutral document")
    if (
        DocumentValue.schema_version != "1.0"
        or DocumentValue.diagnostics
        or DocumentValue.source.attributes
    ):
        raise ValueError(
            "plain part preparation does not admit unresolved or extended source state"
        )
    ProvenanceItems = (
        *(Value.provenance for Value in DocumentValue.parameters),
        *(Value.provenance for Value in DocumentValue.support_planes),
        *(Value.provenance for Value in DocumentValue.sketches),
        *(Value.provenance for Value in DocumentValue.feature_timeline),
        *(Value.provenance for Value in DocumentValue.bodies),
        *(
            EntityValue.provenance
            for SketchValue in DocumentValue.sketches
            for EntityValue in SketchValue.entities
        ),
    )
    if any(Value is not None for Value in ProvenanceItems):
        raise ValueError(
            "plain part preparation does not yet map source record provenance"
        )
    if any(
        BodyValue.topology != TopologyCounts() for BodyValue in DocumentValue.bodies
    ):
        raise ValueError("plain part preparation does not admit supplied body topology")
