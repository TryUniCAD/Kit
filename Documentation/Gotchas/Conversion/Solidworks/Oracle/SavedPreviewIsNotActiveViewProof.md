# Saved preview equality does not establish active view persistence

## Expected

Distinct active-view orientation, translation and scale requests produce distinct saved previews. A saved preview therefore identifies the active view shown on fresh reopening.

## Observed

The [controlled visible view batch](../../../../../re/solidworks/measurements/2026/VisibleViewProbe02.json) passes all five baseline/orientation/scale/translation/combined cases and ten native phases. Every first saved active pose exactly matches the fresh process's initial, rebuilt and post-save active poses. Before/after controls are healthy and licensing process IDs are unchanged.

The [ten original previews](../../../../../re/solidworks/measurements/2026/ViewProbePreparation02.json) disagree with that simple expectation. Baseline, scale, translation and combined cases share the exact same large-cylinder PNG, SHA-256 `2917d8c3a9f0ad2feea5dc0bd93a98923c2e748a4e6521c78fdec4f7cc25e0be`, despite distinct native API poses. The orientation-only case has a different small-cylinder PNG. Every case's first-save and fresh-reopen preview pair is byte-identical. No private application chrome appears. These observations do not identify whether the preview renderer, cache, activation timing or another owner explains the shared image.

## Workaround

Keep active API pose, saved typed fields, saved preview and actual visible viewport evidence separate. Use exact input/process identities and controlled native save/reopen measurements for the API state. Decode the complete archives remotely before identifying a persisted field. Inspect the actual active viewport before claiming visual parity. Bind preview observations to file hashes; identical PNG bytes cannot establish that the underlying native API state is equal.

These diagnostic reader fixtures add zero new writer outputs, held-out evidence or production acceptance. The [workflow entry](../../../../Changes/Solidworks/Inspection/Presentation/SolidworksViewProbeReaderFixtures.md) records their provenance and pending complete decoding.
