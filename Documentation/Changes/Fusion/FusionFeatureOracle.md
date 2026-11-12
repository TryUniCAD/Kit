# Fusion feature schema and geometry evidence

## Behavior

The research workspace now includes controlled circular-sketch and extrusion archives at 7 mm and 13 mm, native entity-property captures, and a same-source native parameter/binding rewrite to 19 mm.
The capture scripts preserve the original active document and close only documents created by the experiment.
The dispatcher propagates script failures to a nonzero process status.

The binary feature-schema extractor records explicit version branches, member names, C++ type evidence, registration addresses, persistence options, and inherited-schema limitations.
It preserves unresolved traces as incomplete evidence.
The [data model](../../Reference/Research/FusionDataModel.md) describes the distinction between registered fields, persisted fields, and cached geometry.

The research-only C++ reflection bridge reads Fusion's existing native registry and member sets through verified exported getters.
The first successful capture contains 1,958 registered metatypes, 260 initialized schemas, and 938 registered fields.
It records field names, declared types, reference categories, option masks, schema versions, and inheritance while preserving uninitialized sets as unknown.
The static extractor independently agrees with the runtime capture on all 80 current fields across its 12 initialized classes, and recovers 38 versioned registration schemas.
The expanded run opened 64 representative corpus archives in separate native tasks and ended with zero open documents.
Its final snapshot contains 488 initialized schemas and 1,910 fields, covering initialized member sets for 401 of the corpus's 403 declared classes.
The two uninitialized classes and every intermediate snapshot digest remain explicit in the coverage and import records.
The reflected research codec decodes and regenerates ten controlled sketch, extrusion, and continuation records: all 1,734 bytes are explained, all 238 native field values agree, and re-encoding from JSON values is byte-identical without residual payload data.
The optional version exporter also captured 494 initialized exact class/version lookups, including six older schemas used by the corpus.
It distinguishes absent from uninitialized entries and does not assign a historical version to a base pointer that exposes none.

## Usage

Run `CaptureFeature.py` and `InspectFeatures.py` through `re/Fusion/LocalOracle/RunNative.mjs` with an installed, running Fusion application.
`PrepareFeature.py` uses only Kit's Python codecs to rewrite the captured source.
`AcceptFeature.py`, dispatched inside Fusion, checks native import, full rebuild, subsequent editing, save, and reopen against the recorded cylinder dimensions and volume.
These scripts operate on their own `Features/` artifacts and require explicit native-oracle authorization.

Build `SchemaBridge.cpp` with the command recorded in `BridgeEvidence.json`, then dispatch `CaptureSchema.py` through the same native bridge.
The capture checks the recorded Fusion build and library digests, requires a new output path, and invokes the compiled bridge on the existing main-thread task.
`SelectSchemas.py` chooses corpus files by missing class declarations; `WarmSchemas.py` imports one selected file per invocation and captures an additional runtime snapshot.
Resumption counts a selected archive as complete only when its matching path and digest have both an opened import attempt and a corresponding schema snapshot. Failed imports and imports without a completed snapshot are retried; their attempts remain in the evidence log.
The [corpus viewport crash](../../Gotchas/Conversion/Fusion/FusionCorpusViewportCrash.md) explains why snapshots are taken per imported document.

`InspectFeatures.py` uses numeric entity identifiers from the active import.
The first JSON-reference query attempt failed for every entity; those counts remain in the original capture report.
The successful replacement capture is separately recorded in `GraphCapture.json` and the entity files.
Named roots are explicitly skipped, and the property visitor can omit fields that do not implement its JSON interface.

## Verification and limitations

Fusion 2706.1.17 exported the three controls and returned 211, 243, and 243 numeric entity-property records without errors; 14, 15, and 15 named roots were skipped.
The [native acceptance record](../../../re/Fusion/LocalOracle/Features/Acceptance.json) verifies a 19 mm rebuilt extrusion, a subsequent 23 mm edit, and 23 mm geometry after save and reopen, retaining the sketch and extrusion timeline entries.
The [geometry-cache gotcha](../../Gotchas/Conversion/Fusion/FusionGeometryCaches.md) records the stale 7 mm body before rebuild.

This adds no complete native document writer or independent BRep generator.
Same-source feature records and geometry caches remain preserved by the research edit.
Archive integration cases run in PR CI; no local automated test suite was run.
Native reflection still does not establish custom serializer bytes, historical migration behavior, or all schemas that have not been initialized by an observed document.
