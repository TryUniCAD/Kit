from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument


# an equally plausible span from another position cannot replace the selected sketch record
def ShiftOwnerSpan(InputDoc: CadDocument) -> CadDocument:
    Features = list(InputDoc.feature_timeline)
    Position = next(
        Index
        for Index, Feature in enumerate(Features)
        if Feature.sketch_id == InputDoc.sketches[0].id
    )
    OwnerValue = Features[Position]
    Provenance = OwnerValue.provenance
    assert Provenance is not None
    (SpanValue,) = Provenance.spans
    Features[Position] = ReplaceValue(
        OwnerValue,
        provenance=ReplaceValue(
            Provenance, spans=(ReplaceValue(SpanValue, offset=SpanValue.offset + 1),)
        ),
    )
    return ReplaceValue(InputDoc, feature_timeline=tuple(Features))
