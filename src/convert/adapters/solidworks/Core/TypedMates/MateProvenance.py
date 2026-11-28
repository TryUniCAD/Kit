from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from interchange import Provenance, ProvenanceSpan


# mate provenance must identify the decoded object record instead of guessing scalar offsets
def MateProvenance(NodeValue: ArchiveNode) -> Provenance:
    StartValue, EndValue = NodeValue.StartOffset, NodeValue.EndOffset
    if StartValue is None or EndValue is None or EndValue <= StartValue:
        raise ValueError("typed mate root has no complete native record span")
    return Provenance(
        adapter="sldasm",
        native_id=str(NodeValue.FieldsValue["f08"]),
        spans=(
            ProvenanceSpan(
                "Contents/Config-0-MatesList",
                StartValue,
                EndValue - StartValue,
                "typed-archive-object",
            ),
        ),
        confidence=1.0,
    )
