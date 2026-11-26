# Persist Fusion encoder writer inputs

## Behavior

The research encoder qualifies its existing constrained Fusion cuboid before it prepares either role.
Each successful preparation produces a typed constructor document with the original source identity.
The runner reloads that role's JSON before the Fusion writer generates the native candidate.
The prepared document contains constructor semantics. The decoded native state remains in `document.json`.

The writer uses the recorded candidate filename and timestamp with the same deterministic constructor.
The source identity stays in the prepared JSON. The writer seeds generation from the constructor fields.
The strict output check remains part of generation.
Schema 2 binds the writer JSON, candidate and source identities to the run fingerprint.
The receipt importer regenerates the candidate bytes from the saved input.

## Usage

Use the [encoder round-trip command](EncoderRoundTripPipeline.md#usage) with `--application fusion`.
Retain `manifest.json`, `document.json`, both role JSON files, the native candidates and the exact native receipts.
Use the [existing receipt subcommand](EncoderRoundTripPipeline.md#attach-native-measurement-evidence) with the recorded role.
Use the same pinned runtime and checkout for exact replay.
The original native source is needed for repeating source qualification.
Receipt replay uses the prepared JSON and does not reopen that source.

## Limits

Earlier schema 1 runs remain eligible for their existing receipt path.
The source restrictions and native publication requirements remain in effect.
The adapter still refuses unsupported saved graphs and does not promote a read-only source into the constructor scope.
Native observations belong to the exact candidate digests and revision-bound receipts that were measured.

## Verification

At `3397cb62c1`, four installed CLI cases passed in 149.05 seconds on Windows with Python 3.14.6.
The cases checked edited and reconstructed replay, no-op refusal, stable fingerprints, and malformed native input.
An independent run removed its temporary native source and generated both roles from persisted JSON in fresh processes.
Both 100,168-byte outputs exactly matched the measured reconstruction and edited Fusion archives in the [native evidence record](../../../../re/Fusion/EncoderRoundTrip/NativeEvidence.md#integrated-cli-reconstruction-and-edit).
The same checkout attached both original schema 1 Fusion receipts to a separate copy of their original run.
Repeating both attachments preserved the manifest and receipt bytes.
Changing role inputs, source identity, or saved geometry withheld receipt attachment even when the artifact hashes and fingerprint were recalculated.
An original schema 1 receipt cannot authorize a different schema 2 run fingerprint.
The refusal probes preserved the output directories without writing receipt sidecars.

At `1810844e4d`, both affected installed CLI cases passed in 115.92 seconds. After the native source was removed, receipt intake reached the expected fingerprint refusal on the intact schema 2 run. Transplanting and rebinding the other role's writer JSON failed candidate regeneration. Both refusals preserved all run and receipt files without creating a sidecar.

For archiving completed Windows test roots, see [pytest retention links](../../../Gotchas/Research/Workers/Windows/PytestRetentionLinks.md).
