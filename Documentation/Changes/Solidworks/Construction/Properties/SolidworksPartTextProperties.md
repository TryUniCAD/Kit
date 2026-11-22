# Construct ordinary SOLIDWORKS part text properties

The internal SDK part composer accepts `PartTextInput` with separate
summary, document and active-configuration text fields. It generates the
three corresponding native XML streams with their own computed values, IDs
and dictionaries. A name can appear independently at both custom scopes.

An ordinary triangle and analytic circle preserve their text through
independent native edits, save and fresh reopen in SOLIDWORKS 2026 SP05.2.
Both controls and all six processes pass. Four guarded SDK workers match
the native-tested thirteen-stream candidates byte for byte and reject eight
unsupported inputs per process. Empty settings preserve existing output.

The internal profile covers literal text in one configuration. Linked
values, equations and other property types require separate qualification.
Public writer admission remains within the qualified ordinary part scope.

[Construction and native evidence](../../../../../re/solidworks/records/SdkPartTextProperties2026.md)
