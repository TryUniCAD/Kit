# The empty sheet-metal keyword row uses a reserved identity

The empty sheet-metal master appears as a `Feature` row with identity
`-1` in 31 disclosed saved parts. Its name and child list are empty.
Config-0 owns the corresponding `moSheetMetalMaster_c` directly at
`f1018`.

Admit the reserved value only for this empty helper. Keep ordinary
positive allocated identities for design features and occurrences.
[Typed corpus evidence](../../../../../../re/solidworks/records/KeywordTypedCorpus2026.md)
