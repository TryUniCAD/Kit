# Deterministic encoder round-trip research pipeline

## Behavior

The research CLI adds `encoder-round-trip` through the existing trusted-checkout launcher.
The pipeline reads a native source with the checkout's SDK and records each stage separately.
It persists neutral JSON, source identity, document identity, a run fingerprint, timing, and precise failure outcomes.
The fingerprint binds SDK `.py`, `.json`, and `.xz` inputs, shared helper files, pipeline files, and the selected adapter.
Runtime identity includes the interpreter, platform, architecture, zlib, and Fusion's standard-library Zstandard version.
Format adapters receive the neutral document and the requested bounded edit.
The source, reconstruction, and edited candidate retain separate statuses.

For eligible SOLIDWORKS roles, the adapter uses the source archive only to qualify the source.
It then builds a typed writer input for each role.
The runner writes `<role>-writer-input.json` and reloads that file before it writes the candidate.
The `writer_input` record for each role gives the relative path, SHA-256 digest, and byte count.
Manifest schema `2` includes a `writer_input_sha256` map keyed by role and binds that map into the run fingerprint.

The pipeline uses deterministic local code.
It has no model provider option or runtime model call.
Its manifest records `models_used: false`.
Candidate generation runs independently of any CAD application.
Licensed native measurement remains a separate research operation.

Each run stages its files privately before publishing an unused output directory.
An occupied destination is refused.
A refused native source publishes its failure report with blocked candidate stages.
A settled output remains immutable when the same command is repeated.
An abandoned private staging directory does not represent a published outcome.
Retry an interrupted run with its original output path only when that path remains absent.

## Usage

Use an installed Python 3.14 CLI and an absolute, trusted research checkout.
The selected checkout must contain both the SDK and the format adapter.
Choose a source file within the adapter's declared bounded scope and an unused output directory.
The depth below is a requested edit in millimetres.

```sh
kit research --root /absolute/KitResearch encoder-round-trip run \
  --application solidworks --source /absolute/Input.SLDPRT \
  --output /absolute/RoundTrip --depth-mm 12.5
```

Select `--application fusion` for a bounded Fusion source.
Inspect `manifest.json` before using a generated candidate.
Inspect `document.json` for the source's decoded neutral representation when decoding succeeds.
The reconstruction and edited candidate use distinct native filenames.
The recorded native locator and fixed timestamp participate in deterministic candidate generation.
For identical fingerprints across output directories, pass the same absolute Windows directory with `--native-locator-directory`.

### Replay a SOLIDWORKS writer input

Keep the original source archive with `document.json` to repeat source qualification.
To regenerate a single candidate, use its `<role>-writer-input.json` with the checkout and runtime recorded in the manifest.
Read `native_locators[role]` and `written_at` from the same manifest.
Choose an unused scratch directory.
This example replays the edited role with a fixed native locator.

```sh
python -I -B /absolute/KitResearch/re/tooling/sw2026/PreparePlainPartEvidence.py \
  --neutral /absolute/RoundTrip/edited-writer-input.json \
  --native-locator 'C:\KitEncoderRoundTrip\edited.SLDPRT' \
  --written-at 1767225600 --scratch /absolute/FreshReplay
```

The preparer opens the typed writer input in a fresh process.
It generates `edited.SLDPRT` and records its SHA-256 digest in `Candidate.json`.
Compare that digest with `candidate_sha256.edited` in the round-trip manifest.
If the digests differ, check the exact locator, epoch, SDK revision, and compression runtime before using the replay.

### Attach native measurement evidence

Attach independently collected native evidence to the corresponding candidate.
The importer checks the receipt's bindings before it retains the evidence.

```sh
kit research --root /absolute/KitResearch encoder-round-trip attach-receipt \
  --output /absolute/RoundTrip --role reconstruction \
  --receipt /absolute/ReconstructionReceipt.json
```

Use `--role edited` for the edited candidate.
The generic native receipt requires schema `1`, application, role, SDK revision, run fingerprint, source digest, and candidate digest.
It also requires a candidate observation and before-and-after observations of one independent control.
All observations must report one application build and distinct positive process identifiers.
Each observation uses the existing native measurement record contract.
The importer rechecks the persisted neutral and candidate bytes against their manifest digests.
It accepts earlier schema `1` run manifests and schema `2` manifests with writer-input evidence.
For schema `2` SOLIDWORKS runs, the importer validates each saved writer input.
It regenerates each completed role with its recorded native locator and creation epoch.
The regenerated bytes must match that role's saved candidate before the importer retains a receipt.
A failed role can retain its checked writer input and diagnostics.
It must have no candidate file, digest, or artifact record.
Use the SDK checkout and compression runtime that reproduce the recorded bytes.
It retains an accepted receipt as `<role>-receipt.json` without modifying the manifest.
An identical attachment is idempotent.
A different receipt for an occupied role is refused.

For SOLIDWORKS, the same command also accepts the exact SDK envelope containing `written_at` and `receipt`.
The importer applies the SDK's oracle identity and exact candidate checks.
It compares the candidate header's creation epoch and locator with the manifest.
The response records `measurement_status: exact_sdk_candidate_bound` and supplies the receipt option and locator for SDK publication.
Pass the unchanged envelope as `values["solidworks_native_measurement"]` when publishing a complete strict cold readback of that candidate.
Use the exact measured locator for the destination.

Keep the source, typed writer inputs, and candidate files with their manifest and receipts.
Follow the [deterministic research procedure](../../../Tasks/ResearchCommandLine.md) for the existing entry points.

## Limits and acceptance

This delivery provides shared research orchestration.
Each format adapter defines its own supported source semantics and edit boundary.
Unsupported semantic changes retain an explicit refusal.
Each candidate adapter must derive its emitted fields from format knowledge without a donor fallback.
The shared pipeline rejects an edit identical to its reconstruction.
An independently generated reconstruction can match a deterministic qualified source byte for byte.

Exit `3` records an incomplete research outcome, including source rejection or unavailable candidate generation.
Exit `1` reports invalid inputs, unsafe output publication, or rejected receipt bindings.
Argument syntax errors use exit `2`.
Generated candidates retain pending native acceptance.
Byte identity, successful SDK reads, and attached receipt files do not establish editable native conversion.

The shared manifest and receipt attachment results retain `vendor_loadable: false` and `application_usable: false`.
Complete independent native acceptance remains a separate obligation.
Apply every [CAD success criterion](../../../Reference/Operations/CadSuccessCriteria.md) before claiming a format milestone.
Required evidence includes fresh-process loading, healthy controls, rebuild results, body measurements, feature history, and a driving edit.
This change does not complete the production conversion roadmap.

## Verification

Verification of writer-input persistence and replay is pending on this revision.
The replay check must generate both SOLIDWORKS roles in independent processes using their saved writer inputs, locators, and epoch.
Each replay must reproduce the archived candidate and its recorded digest.
Receipt attachment verification must also cover a replacement writer input whose manifest digests have been recalculated.
The attachment must refuse the replacement if it regenerates different native bytes.
An isolated CLI check attached a genuine receipt to schema `2` and schema `1` runs.
Both role substitutions were refused after their writer hashes and run fingerprints were recomputed.
The refusals preserved all package files.
Use the existing native measurements to qualify candidates through the separate exact SDK receipt gate.

Installed CLI process coverage lives in `tests/CliResearch/EncoderRoundTrip/`.
It covers malformed native input, blocked candidates, disabled models, invalid driving values, occupied destinations, and preservation of settled outcomes.
The fresh constrained Fusion control requires successful generation in two independent installed CLI processes.
It checks matching candidate bytes, canonical JSON, and source/runtime fingerprints.
Fresh SDK-authored constrained cuboids add positive installed-CLI coverage for reconstruction and a changed driving height.
Both candidate files are read strictly and checked against independently calculated volume and eight corner coordinates.
The checks also require the driving parameter link and the cuboid's solid, face, edge, and vertex counts.
A no-op edit must retain the reconstruction, refuse the edited candidate, and preserve the source and settled output on retry.
An abandoned-directory fixture checks retry behavior without claiming an actual interrupted-process measurement.
These cases use the existing complete-suite collector, merge-queue planner, shards, and completeness report.
The existing Windows research CLI compatibility roster also collects the encoder tests.
Its shards use the installed CLI and a separate research checkout at the candidate revision.
No workflow or CI job is added.

On Windows, pinned Python 3.14.6 collected all 14 encoder cases.
Git Bash validated the Windows roster script syntax.
The existing sort and partition steps assigned the collected encoder cases across four disjoint shards of 4, 4, 3, and 3.
Hosted Windows execution remains separate evidence.

Black 26.10.1 formatted and checked all nine coverage files with exit `0`.
Python 3.11 syntax parsing passed for those files.
Prettier 3.10.1 formatted and checked this change entry with exit `0`.
A Python 3.14.6 CLI process decoded the tracked `SavedCuboid.f3d` source with SHA-256 `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31`.
Its persisted neutral JSON had SHA-256 `db52e0b20372e1d94b7f614d230c22761d1a251773a829b0ce024aba4ea9d04f`.
The shared-only checkpoint returned exit `3` because its format adapter was unavailable.
This observation establishes source transport only.
The older `PublicAdapter/cuboid.f3d` control was explicitly rejected.
A separate synthetic-package CLI smoke checked candidate digest refusal, consistent receipt ingress, idempotent attachment, and conflicting-receipt preservation.
The synthetic observations retained both acceptance flags as false and provide no vendor measurement evidence.
An isolated CLI process attached both authentic SP04.1 held-out receipts using the exact candidate bytes and SDK gate.
The process verified wrong-role, wrong-build, changed-epoch, changed-locator and conflicting-receipt refusals.
Identical retries returned the same bindings and preserved the original manifests and envelopes.
The installed CLI regression prepares the held-out input and checks the exact envelope path against the measured digest.
When the active compressor generates different bytes, the genuine receipt must refuse publication of a receipt sidecar.
The isolated installed-wheel CLI suite passed all fourteen cases in 248.27 seconds at revision `9b944f277f`.
The package and separate research checkout used the same pinned revision with Python 3.14.6.
After the receipt validation repair, the affected installed CLI case passed in 53.39 seconds at `0f08f80eed`.
Both public SOLIDWORKS publication cases passed after the central SDK numeric repair.
An instrumented Python 3.14.6 CLI child was held before opening its staged manifest after neutral JSON was written.
The owning harness terminated that research child; the outer process returned `15` and the final destination remained absent.
The private stage remained unpublished.
A normal retry to the same output returned incomplete exit `3` on the shared-only checkout without a format adapter.
The retry retained the same neutral JSON digest.
The process observation used SDK revision `82339a9892238ab3f0dcf841bd2295a6f54008a9` with the shared provenance changes present.
It establishes interrupted publication and retry behavior, with native qualification unchanged.
Remote process results, current-revision CI, configured review, and merge-group acceptance remain pending.
Complete native acceptance remains unmeasured by this shared package.
Documentation was inspected as source.
Rendered usability and complete language conformance remain unverified.

## Integrated CLI verification

The normal research CLI passed for both formats at integration revision `a529ff98cb7624982bb05a41c1ab7c07eaed6a38`.
Both runs used Python 3.14.6 with zlib-ng and recorded `models_used: false`.
SOLIDWORKS generated both candidates in 17.82 seconds, including 14.41 seconds for source decoding and JSON persistence.
Fusion generated both candidates in 43.32 seconds, including 9.22 seconds for source decoding and JSON persistence.
Both manifests retained `awaiting_native` status.
These process measurements cover the integrated command and its declared bounded inputs.
The strengthened installed replay case passed in 76.25 seconds at revision `6eaaa3cd63`.
Both independent runs produced matching non-null native candidate hashes and preserved their source.

## Ownership

The shared orchestration belongs to assignment 1 of `Encoder20261125`.
The shared pipeline owner coordinates its delivery PR and owning-register reconciliation.
The SOLIDWORKS and Fusion adapters retain separate format owners and acceptance evidence.
Dependencies are the existing research launcher, SDK readers, deterministic candidate adapters, and independently measured native receipts.
The bounded exit requires revision-bound shared process evidence and the applicable PR gates.
Full format acceptance retains the criteria above.
