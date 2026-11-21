# Width predicates retain unordered comparison flags

A mathematical reading of the custom-line-width predicate suggests that it accepts only a positive float with width code ten. The exact current native leaf instead compares zero with the stored float and branches on carry before testing that code. Finite values follow the positive-width interpretation; unordered comparisons also set carry if the comparison completes.

The first private proof used the stronger ordered-positive shorthand. Its corrected metadata retains the actual flag condition and leaves floating exception masking and pathological NaN behavior unqualified. All 4,350 executable sources are unchanged between those proof revisions.

When documenting or reconstructing this path, keep the native comparison flags distinct from a high-level ordered comparison. Preserve source wire fields in the raw codec; do not invent NaN rejection, cache values, or constructor domains from this predicate alone.

The [native line-font evidence](../../../../../../../re/solidworks/records/DrawingLineFontArchive2026.md) binds the complete leaf, caller, and post-read cache owner to the exact installed module hash.
