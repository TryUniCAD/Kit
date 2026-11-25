from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument


# a disagreement in the native sketch identity must withhold the evidence without changing the owner link
def ChangeSketch(Document: CadDocument) -> CadDocument:
    (SketchValue,) = Document.sketches
    assert (
        SketchValue.provenance is not None and SketchValue.provenance.native_id == "26"
    )
    NewProvenance = ChangeRecord(SketchValue.provenance, native_id="27")
    return ChangeRecord(
        Document, sketches=(ChangeRecord(SketchValue, provenance=NewProvenance),)
    )
