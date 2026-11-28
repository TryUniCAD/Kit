# SOLIDWORKS downstream constructor state

The [exact-build research record](../../../../../re/solidworks/records/DownstreamConstructorEnable2026.md) now distinguishes the final `moDownstreamIdData_c` constructor prefix from its earlier zero stores and binds the native enable predicate. Its data-only companion supplies complete native extents, original-image hashes, instruction-window hashes and import identities.

The constructor calls the native current-version and full-date-code producers, sets two later prefix words to `101`, constructs the local-calendar 1990 sentinel time and retains the supplied model owner. The enable rule combines an unresolved application virtual result with an initialized dump-option flag. Neither an enabled default nor a universal UTC timestamp is inferred.

Use this knowledge when modeling constructor provenance or reviewing downstream initialization. The [constructor-prefix gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/ConstructorPrefixIsNotFinalState.md) describes the corrected assumption. The existing standalone-read map and body-grammar records remain unchanged.

Verification used original-PE metadata and instruction inspection with zero native runs and zero hidden-source reads. The actual standalone save caller, full populated construction rule and native held-out acceptance remain open.
