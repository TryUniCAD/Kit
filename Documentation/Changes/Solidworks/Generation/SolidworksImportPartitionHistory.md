# SOLIDWORKS local import partition history

The internal SDK generates the body-free configuration partition for a
version-19000 local import. `MakeImportHist` accepts fresh activation followed
by local attachment and returns both framed Parasolid transmits with the
activation and selected mark IDs needed by the native archive composer.
The constructor computes mark links, allocation and schema fields from
the measured history rules. [Usage and grammar](../../../../re/solidworks/records/SdkImportHistory2026.md)

Two offline runs matched the 606-byte stream from the independent fresh
history builder and all four generated part containers. Both archive mark
owners agreed with the generated IDs. Fourteen out-of-profile requests
were refused, and construction recorded zero guarded file reads. This
component covers fresh local imports with body-free rollback.
[Measurements](../../../../re/solidworks/measurements/2026/SdkImportHistory01.json)
