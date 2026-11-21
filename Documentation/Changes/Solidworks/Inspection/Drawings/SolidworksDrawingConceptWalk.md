# SOLIDWORKS drawing concept walk

The research command `PYTHONPATH=src python re/tooling/sw2026/serial/CheckDrawingPrefix.py CORPUS` walks the typed SOLIDWORKS 2026 Definition graph through its ordered sheet and model-view list. It verifies native orientation, view scale, model-to-view transform, and external part ownership on the two disclosed views. An empty-sheet control checks the same native list boundary without a view.

All three prefixes round-trip exactly in memory. The [concept prefix record](../../../../../re/solidworks/records/DrawingConceptPrefix2026.md) documents the shared class dependencies, their scope and the verification receipt. The public SDK continues to offer the separately qualified layout inspection.
