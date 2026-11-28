# Reuse completed Hopper analysis for the markup constructor

Initial analysis of the pinned SOLIDWORKS 2026 modelling DLL exceeded REA's
900-second startup window. Hopper finished analysis separately. The completed
database was saved outside the checkout, reopened through Hopper's native app,
and selected by its unique database path. Hopper's own API then decompiled the
markup constructor at `0x4beae190` in under one second.

The [retained receipt](../../../../../re/solidworks/measurements/2026/MarkupHopperAnalysis01.json)
records the REA startup and close results, database hash, native procedure
identity and decompilation hash. The successful output corroborates the base
constructor call, both class-table assignments and the scalar initialization
in the [format record](../../../../../re/solidworks/records/MarkupFolderConstruction2026.md).
Original instruction spans establish the byte offsets and boundaries.

The saved database and decompiled result stay outside every checkout.
This analysis made no serializer or production adapter change.
