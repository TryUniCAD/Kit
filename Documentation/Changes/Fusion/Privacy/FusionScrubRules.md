# Scrubber rules for truncated keys in material stores

## Behavior

[`ScrubSaved.py`](../../../../re/Fusion/LocalOracle/ScrubSaved.py) now finds residue values whose key was cut where a block's unused capacity begins in a protein `AssetData` property store.
A value after a key suffix of two or more characters of a known account or name key is replaced as if the whole key were present.
A value of 6 to 40 letters and digits after a bare `": "` at the start of the unused capacity is also replaced.
Both rules read only the unused capacity that each block header leaves after its used bytes.
In `AssetData` members that are not block stores, the suffix rule reads the whole member and the bare-value rule is off.
The fragment search is now also confined to that unused capacity, so no used material byte can change.
Values found by the new rules feed the fragment search only when they mix letters and digits.

The [scrub ledger](../../../../re/Fusion/LocalOracle/ScrubLedger.json) now lists every placeholder already written.
The scrubber leaves values inside those placeholders unchanged, so a second run over a scrubbed archive changes no byte.
The scrubber reads the ledger beside it unless `--ledger` names another, and the ledger's reason text records how residue is delimited.

## Effect

A dry run over the Fusion archives that this branch added found new replacements in 16 of them: 14 that were already in the ledger and 2 new ones.
Each replacement was residue text such as a parameter, feature or telemetry event name or a product version.
A dry run over archives that are already on `main` also proposed replacements; this entry does not change them.
The [protein residue gotcha](../../../Gotchas/Conversion/Fusion/Records/FusionProteinHeapResidue.md) describes the block layout.

## Verification

`ReadDocument` models and `EmitParsed` round trips stayed equal for all 16 changed archives.
`ReadFusionDoc` documents differed only in the whole-archive digest and passthrough payload.
A second run over the 173 ledger archives, and over the 734 tracked Fusion archives that are not on `main` apart from one third-party bundle, changed no byte.

Static checks ran locally; no local automated tests were run.
