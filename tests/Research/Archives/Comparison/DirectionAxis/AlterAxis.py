from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.DirectionAxis.ChangeNormal import ChangeNormal


# each isolated fault changes one direction ownership assertion in the decoded source
def AlterAxis(Document: CadDocument, FaultName: str) -> CadDocument:
    if FaultName == "normal":
        return ChangeNormal(Document)
    (Selection,) = Document.selections
    Provenance = Selection.provenance
    assert Provenance is not None
    if FaultName == "provenance":
        (SpanValue,) = Provenance.spans
        Changed = ChangeRecord(
            Selection,
            provenance=ChangeRecord(
                Provenance,
                spans=(ChangeRecord(SpanValue, offset=SpanValue.offset + 1),),
            ),
        )
    elif FaultName == "owner":
        Changed = ChangeRecord(
            Selection,
            query={**Selection.query, "native_owner_id": 2},
            provenance=ChangeRecord(Provenance, native_id="2:axis:N_Axis"),
        )
    else:
        assert FaultName == "target"
        Changed = ChangeRecord(
            Selection, query={**Selection.query, "native_target_id": 2}
        )
    return ChangeRecord(Document, selections=(Changed,))
