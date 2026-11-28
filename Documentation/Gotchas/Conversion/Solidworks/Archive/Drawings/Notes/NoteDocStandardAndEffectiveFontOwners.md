# Note document standard and effective font have separate owners

Expectation: a drawing with a `moANSI_c` Definition UI owner uses matching ANSI model detail settings, and the note uses the first font found in that detail graph.

Actual: the disclosed generated file has that UI owner with model `fae0.f10=1`; native save changes its UI owner to `moISO_c`. The four disclosed originals/edits have `fae0.f10=0` and `moANSI_c`. Their Segoe UI helper formats are independent from the Century Gothic format actually selected for kind-21 ordinary notes.

The source-bound getter selects the effective model detail pointer, then its `f1f18.f418.f50` note format. The source format height/spacing is `.003175/.001`, whereas the generated pair uses `.0035/0`. Root `f90` and the separate helper formats must not be substituted for that actual owner. Runtime effective-detail overrides remain an explicit observation boundary.

Preserve the selector, UI class and each font/spacing owner separately. Use the complete independently proven ANSI operation where admitted, then model or reject the remaining source settings; changing only one selector is insufficient. See [the numeric evidence and inventory](../../../../../../../re/solidworks/records/DrawingPlainNotePresentation2026.md). No constructor or public-admission change is made by this record.
