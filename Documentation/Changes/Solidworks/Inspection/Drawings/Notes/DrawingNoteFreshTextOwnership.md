# Drawing note fresh text ownership

The new [source record](../../../../../../re/solidworks/records/DrawingNoteFreshText2026.md) separates last-newline handling from the glyph-box dirty state, binds the actual note display path to box measurement, and records fresh text/paragraph construction and font-derived metric ownership for the exact SOLIDWORKS 2026 build.

Use these independently derived rules when preparing a complete disclosed note experiment. The load-time `f160|2` fixup is the last-newline flag. Box recomputation uses mask `1`. Constructor metric zeros do not establish saved-neutrality or native first-open behavior. The [specific gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/Notes/NoteLastNewlineIsNotGlyphDirty.md) records that distinction.

A static original-PE replay passed for three modules, 36 complete functions, 19 instruction windows, one vocabulary range, 20 imports and six virtual cells. No SDK/schema/codec execution, tests, native run or sealed-source access occurred. Existing note byte/map/alias retention and normal semantic refusals remain unchanged. There is no note writer, native acceptance, portable font-metric qualification or new public drawing admission in this delivery.
