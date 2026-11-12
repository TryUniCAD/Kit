# Fusion feature schema and geometry evidence

## Behavior

The research workspace now includes controlled circular-sketch and extrusion archives at 7 mm and 13 mm, native entity-property captures, and a same-source native parameter/binding rewrite to 19 mm.
The capture scripts preserve the original active document and close only documents created by the experiment.
The dispatcher propagates script failures to a nonzero process status.

The binary feature-schema extractor records explicit version branches, member names, C++ type evidence, registration addresses, persistence options, and inherited-schema limitations.
It preserves unresolved traces as incomplete evidence.
The [data model](../Reference/Research/FusionDataModel.md) describes the distinction between registered fields, persisted fields, and cached geometry.

## Usage

Run `CaptureFeature.py` and `InspectFeatures.py` through `re/Fusion/LocalOracle/RunNative.mjs` with an installed, running Fusion application.
`PrepareFeature.py` uses only Kit's Python codecs to rewrite the captured source.
`AcceptFeature.py`, dispatched inside Fusion, checks native import, full rebuild, subsequent editing, save, and reopen against the recorded cylinder dimensions and volume.
These scripts operate on their own `Features/` artifacts and require explicit native-oracle authorization.

`InspectFeatures.py` uses numeric entity identifiers from the active import.
The first JSON-reference query attempt failed for every entity; those counts remain in the original capture report.
The successful replacement capture is separately recorded in `GraphCapture.json` and the entity files.
Named roots are explicitly skipped, and the property visitor can omit fields that do not implement its JSON interface.

## Verification and limitations

Fusion 2706.1.17 exported the three controls and returned 211, 243, and 243 numeric entity-property records without errors; 14, 15, and 15 named roots were skipped.
The [native acceptance record](../../re/Fusion/LocalOracle/Features/Acceptance.json) verifies a 19 mm rebuilt extrusion, a subsequent 23 mm edit, and 23 mm geometry after save and reopen, retaining the sketch and extrusion timeline entries.
The [geometry-cache gotcha](../Gotchas/Conversion/FusionGeometryCaches.md) records the stale 7 mm body before rebuild.

This adds no complete native document writer or independent BRep generator.
Same-source feature records and geometry caches remain preserved by the research edit.
Archive integration cases run in PR CI; no local automated test suite was run.
