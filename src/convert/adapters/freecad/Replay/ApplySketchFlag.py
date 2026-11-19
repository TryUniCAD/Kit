from __future__ import annotations

from dataclasses import replace as Replace

from interchange.document.Models.DocumentModel import CadDocument


# only an inherited sketch flag follows the archived model when suppression semantics change
def ApplySketchFlag(
    DocValue: CadDocument, Before: CadDocument, After: CadDocument
) -> CadDocument:
    OldFlags = {Sketch.id: Sketch.suppressed for Sketch in Before.sketches}
    NewFlags = {Sketch.id: Sketch.suppressed for Sketch in After.sketches}
    Sketches = tuple(
        (
            Replace(Sketch, suppressed=NewFlags[Sketch.id])
            if OldFlags.get(Sketch.id) is Sketch.suppressed and Sketch.id in NewFlags
            else Sketch
        )
        for Sketch in DocValue.sketches
    )
    return Replace(DocValue, sketches=Sketches)
