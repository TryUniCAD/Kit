# Radial constructors replace empty display prefixes

## Expectation

The shared display constructor initializes the prefix string as empty.
Reusing that state for a radial display could appear sufficient.

## Observed behavior

The 2026 radial constructor performs another prefix assignment after its position update.
The ordinary radius prefix becomes `R`.
The ordinary diameter prefix becomes `<MOD-DIAM>` with the constructor's default format selector.
The setter writes the primary string at runtime `+0x7f8`, serialized as `f7f8`.

The native diameter token is markup.
Replacing it with a Unicode glyph or a literal letter changes the format vocabulary.
The constructor also sets a separate instance-count flag after this assignment.

## Workaround

Follow the complete constructor order for the actual display class.
Derive the prefix from the dimension mode and the native format vocabulary.
Keep runtime-only selectors separate from current archive fields.
Validate the complete generated display in the native application before claiming acceptance.

The [2026 presentation record](../../../../../re/solidworks/records/RadialPresentationConstruction2026.md)
contains module hashes, function extents, resource identity and exact assignment boundaries.
