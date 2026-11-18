# Retained detailing indices remain unprojected

A fully typed native detailing index can retain model keys, component text, downstream kernel IDs and actual edge-reference objects without resolving those IDs to portable child topology. Removing an empty-index restriction does not establish that geometric resolution.

The bounded reader preserves every native row and alias and exposes `drawing.detailing_edges` as unprojected content whenever a section is present. It does not rewrite keys into selection strings, infer filenames, substitute feature IDs, drop null rows or claim neutral edge semantics. Unsupported references and malformed maps still fail explicitly.

Keep raw byte/map identity, native index ownership, portable projection and native writer qualification separate. Both disclosed originals currently retain a later annotation/display failure. The [exact field ledger](../../../../../../../re/solidworks/records/DrawingDetailingIndexRead2026.md) records this boundary and the unchanged guards.
