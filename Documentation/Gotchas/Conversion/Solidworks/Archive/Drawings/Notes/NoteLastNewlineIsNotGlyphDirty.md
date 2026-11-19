# Note last newline is not glyph dirty

The generic text loader sets `f160|2`, but the exported `isUseLastNewLine` accessor owns that bit. It does not request glyph-box layout. `setBoxNeedsUpdated`, the actual text-format invalidation virtual, `getBoxInfo` and `updateBoxInfo` use the distinct mask `1`.

A constructor starts dirty and creates text tokens, but a deserialization factory's zero metrics are not a complete nonempty note or a proved valid saved cache. Preserve the actual token graph, effective format, dirty predicates and display context. Measure first-open rendering and save/fresh-reopen behavior before claiming that the application will regenerate a zero cache.

The [exact-build source record](../../../../../../../re/solidworks/records/DrawingNoteFreshText2026.md) pins the constructor, loader, accessors and note-specific display chain. No captured glyph table or broad regeneration rule is justified by this finding.
