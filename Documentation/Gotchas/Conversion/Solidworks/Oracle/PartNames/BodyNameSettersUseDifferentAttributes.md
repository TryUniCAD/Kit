# Body name setters use different attributes

The `setName` and `setSWBodyName` exports take the same input type on
the body wrapper. Their attribute lookup keys differ. Independently
renaming two solid bodies through the native API produced a kind-84
character vector on the actual body under `SDL/TYSA_NAME`. Tracing the
`setSWBodyName` export reaches the separate `SW_INTERNAL_BODY_NAME`
definition.

Bind the requested native property to its saved owner and confirm it
with an authored save and fresh reopen. The native partition compares
both explicit labels and their unchanged driver geometry.

[Saved name archive proof](../../../../../../re/solidworks/records/PartDriverAndBodyNames2026.md)
