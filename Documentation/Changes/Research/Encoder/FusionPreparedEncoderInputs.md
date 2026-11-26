# Persist Fusion encoder writer inputs

## Behavior

The research encoder qualifies its existing constrained Fusion cuboid before it prepares either role.
Each successful preparation produces a typed constructor document with the original source identity.
The runner reloads that role's JSON before the Fusion writer generates the native candidate.
The prepared document contains constructor semantics. The decoded native state remains in `document.json`.

The writer uses the recorded candidate filename and timestamp with the same deterministic constructor.
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
