# Native cache equality is checked before body binding

`ReadBodyCache` compares a fresh native partition decode with the unbound public B-rep. `BindBodyName` subsequently assigns the actual neutral design-body identity and provenance to that B-rep body. Repeating the pre-binding cache equality check on the already bound public result therefore rejects with `public geometry does not match the selected native partition`.

This is not evidence that the payload or geometry changed. Keep the pre-binding cache check in its existing place, and validate the final named document using the complete B-rep owner and topology checks. Do not clear real body ownership to make a second pre-binding call pass.

The ordinary public read and [guarded process proof](../../../../../../re/solidworks/measurements/2026/SdkRevolveBodyNamesProcess01.json) cover the full lifecycle inside one call. The raw native payload hashes remain identical to the preceding reader.
