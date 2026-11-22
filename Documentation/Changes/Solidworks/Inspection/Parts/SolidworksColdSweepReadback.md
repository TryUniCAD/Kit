# Typed SOLIDWORKS cold sweep readback

SDK reads of the canonical cold Standard quarter-arc sweep retain
its ordered section and path, two independently editable D1 parameters,
body density, support frames, configuration and typed native provenance.
With B-rep included, the SDK derives a closed three-face solid from the
two curves. Its two circular rims use neutral seam anchors while the
native topology retains zero physical vertices.

Both full and design-only reads can republish the exact measured archive
through the normal SOLIDWORKS write API. Supply the original measured
locator and in-memory native receipt as for a neutral authored sweep.
Publication compares the complete canonical regenerated source
projection, covering the derived B-rep and provenance wherever present.

The two disclosed files passed direct and registry reads in strict and
permissive mode and measured stream republication with and without B-rep.
The density provenance points to the part material's configuration object.
The reader refuses missing or substituted ghost shapes and extra unmodeled
archive state in strict mode. The saved result partition in six disclosed
native saves triggers an explicit strict refusal. Permissive inspection of
those saves still exposes the legacy inventory.

[Exact readback and source evidence](../../../../../re/solidworks/records/ScopedSweepReadback2026.md)
