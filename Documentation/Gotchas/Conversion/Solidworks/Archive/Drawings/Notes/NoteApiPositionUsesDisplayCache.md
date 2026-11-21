# Note API position uses display cache

A nonzero typed text point does not alone establish the note position returned by the ordinary public API. The disclosed generated diagnostics opened cleanly and preserved Unicode text, yet reported zero `GetPosition` and `GetTextPoint2` both before and after rebuild. An independently supplied name fixed naming without fixing position.

In the exact 2026 plain-note route both APIs reach display virtual `+0x4c0`. For the selected identity frame it computes `f290 + f628*f630`; it does not read `moDimText_c.f38`. The attachment-location cache reads `f290` when its optional array has at most one row, even if a row zero exists. Its separate absolute attachment owner is not a substitute.

Construct the requested geometry using actual owners and derive the display direction and distance from the actual cached attachment in the actual frame. The positively bound point setter normalizes its eligible local displacement into `f628` and writes its norm into `f630`. Preserve the separate text point and glyph/layout owners. Keep mode-dependent z and view transformations guarded; do not make all frames identity or force a saved point into a cache.

The [source record](../../../../../../../re/solidworks/records/DrawingPlainNotePositionOwners2026.md) includes the exact setter/getter chain, hashes and failed diagnostic receipts. Four disclosed source rows corroborate the planar formula, but native/held-out qualification of a new generated positioned note remains separate.
