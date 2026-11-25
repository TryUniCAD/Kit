from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument


# mismatched provenance must withhold ownership evidence while preserving the typed sketch and its graph link
def ChangeSketch(Document: CadDocument, ModeName: str) -> CadDocument:
    (SketchValue,) = Document.sketches
    Provenance = SketchValue.provenance
    assert Provenance is not None and Provenance.native_id == "26"
    if ModeName == "span":
        (RecordSpan,) = (
            Value for Value in Provenance.spans if Value.record_kind == "sketch-record"
        )
        NewSpan = ChangeRecord(RecordSpan, offset=RecordSpan.offset + 1)
        NewProvenance = ChangeRecord(
            Provenance,
            spans=tuple(
                NewSpan if Value is RecordSpan else Value for Value in Provenance.spans
            ),
        )
        assert NewProvenance.native_id == Provenance.native_id
    else:
        assert ModeName == "identity"
        NewProvenance = ChangeRecord(Provenance, native_id="27")
    return ChangeRecord(
        Document, sketches=(ChangeRecord(SketchValue, provenance=NewProvenance),)
    )
