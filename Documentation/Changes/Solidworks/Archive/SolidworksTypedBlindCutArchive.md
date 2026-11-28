# Typed SOLIDWORKS blind-cut archive

The linked SDK archive codec reads and writes the version-19000 records reached by an ordinary blind circular pocket. It preserves the cut's `moICE_c` class tag, its inherited extrusion fields, the affected-body wrapper and the two concrete surface identifiers. The resolved stream extends the map from the actual configuration graph.

Use the published source hash to run the scoped comparison on a disclosed part.

```sh
python re/tooling/sw2026/InspectSdkBlindCutArchive.py INPUT.SLDPRT --sha256 SOURCE_SHA256
```

Four fresh SDK processes compared Config-0 and ResolvedFeatures byte for byte on three vendor saves and one generated discovery part. All eight comparisons preserved their archive map counters and completed with every reached class bound. Neutral cut construction, public feature projection and held-out native qualification remain open. [Measurements](../../../../re/solidworks/measurements/2026/SdkOrdinaryBlindCutArchive01.json) [Record rules](../../../../re/solidworks/records/OrdinaryBlindCutConstruction2026.md#linked-sdk-archive)
