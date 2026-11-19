# Note text has wire specific scalars

A runtime byte or boolean in note text can occupy a `u16` on the wire. Line and character metrics use three `f32`, while the generic text-list helper uses four `f64`. Paragraph alignment fields narrow native integers to `u16`. A character is one unsigned UTF-16 code unit. Substituting runtime structure sizes or flattening tokens into one string loses exact data.

Generic text also stores a real object-list tag and an actual display-item backlink. The backlink can close a cycle to the note already being decoded. The paragraph is embedded without an optional pointer tag. Favorite handle payload is two signed32 words and one unsigned32 word; the runtime handle address is absent.

Preserve raw words and actual archive object identities. Native load ORs bits and normalizes several booleans after consuming the bytes; those effects are not saved defaults. For the attached curve, use the separately proved component-edge wrapper branch rather than broadening the part anchor's sketch-only selection rule.

The [exact-build source and five disclosed Definition round trips](../../../../../../../re/solidworks/records/DrawingNoteTextDependencies2026.md) retain the current field widths, inherited contexts and full semantic refusals. Structural retention does not qualify a fresh note writer or neutral semantic projection.
