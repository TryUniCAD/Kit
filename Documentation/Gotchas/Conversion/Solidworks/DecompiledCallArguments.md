# A decompiler can omit an archive argument

## Expectation

A virtual call without an archive argument in pseudocode cannot read archive bytes.

## Observed behavior

The 2026 part restore calls bridge slot `+0x648` after version `0x1481`.
Its pseudocode shows the bridge and model arguments only.
The instructions at `sldmodu.dll` addresses `0x4c238177` through `0x4c238180`
also pass the archive in `r8`.
The bridge implementation reads a signed count and tagged sheet-metal records.
Omitting that count made all eight measured configuration streams four bytes short.
See the [remote measurement](../../../../re/solidworks/measurements/ArchiveRoundTrip2026.md).

## Workaround

Check argument registers at indirect calls before excluding them from serialization analysis.
Resolve the vtable target and follow its binary reads.
Add typed fields and their count rule. Do not use padding to close a section deficit.
