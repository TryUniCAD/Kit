# Deterministic encoder round-trip research pipeline

## Behavior

The research CLI adds `encoder-round-trip` through the existing trusted-checkout launcher.
The pipeline reads a native source with the checkout's SDK and records each stage separately.
It persists neutral JSON, source identity, document identity, a run fingerprint, timing, and precise failure outcomes.
Format adapters receive the neutral document and the requested bounded edit.
The source, reconstruction, and edited candidate retain separate statuses.

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

Attach independently collected native evidence to the corresponding candidate.
The importer checks the receipt's bindings before it retains the evidence.

```sh
kit research --root /absolute/KitResearch encoder-round-trip attach-receipt \
  --output /absolute/RoundTrip --role reconstruction \
  --receipt /absolute/ReconstructionReceipt.json
```

Use `--role edited` for the edited candidate.
The receipt requires schema `1`, application, role, SDK revision, run fingerprint, source digest, and candidate digest.
It also requires a candidate observation and before-and-after observations of one independent control.
All observations must report one application build and distinct positive process identifiers.
Each observation uses the existing native measurement record contract.
The importer rechecks the persisted neutral and candidate bytes against their manifest digests.
It retains an accepted receipt as `<role>-receipt.json` without modifying the manifest.
An identical attachment is idempotent.
A different receipt for an occupied role is refused.
Keep the source and candidate files with their manifest and receipts.
Follow the [deterministic research procedure](../../Tasks/ResearchCommandLine.md) for the existing entry points.

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
Apply every [CAD success criterion](../../Reference/Operations/CadSuccessCriteria.md) before claiming a format milestone.
Required evidence includes fresh-process loading, healthy controls, rebuild results, body measurements, feature history, and a driving edit.
This change does not complete the production conversion roadmap.

## Verification

Installed CLI process coverage lives in `tests/CliResearch/EncoderRoundTrip/`.
It covers malformed native input, blocked candidates, disabled models, invalid driving values, occupied destinations, and preservation of settled outcomes.
The strict saved-cuboid Fusion control checks neutral JSON and fingerprint consistency across two independent processes.
An abandoned-directory fixture checks retry behavior without claiming an actual interrupted-process measurement.
These cases use the existing complete-suite collector, merge-queue planner, shards, and completeness report.
No workflow or CI job is added.

Black 26.10.1 formatted and checked all eight coverage files with exit `0`.
Python 3.11 syntax parsing passed for those files.
Prettier 3.10.1 formatted and checked this change entry with exit `0`.
A Python 3.14.6 CLI process decoded the tracked `SavedCuboid.f3d` source with SHA-256 `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31`.
Its persisted neutral JSON had SHA-256 `db52e0b20372e1d94b7f614d230c22761d1a251773a829b0ce024aba4ea9d04f`.
The shared-only checkpoint returned exit `3` because its format adapter was unavailable.
This observation establishes source transport only.
The older `PublicAdapter/cuboid.f3d` control was explicitly rejected.
A separate synthetic-package CLI smoke checked candidate digest refusal, consistent receipt ingress, idempotent attachment, and conflicting-receipt preservation.
The synthetic observations retained both acceptance flags as false and provide no vendor measurement evidence.
No local tests, test collection, or licensed native measurements were executed for this entry.
Remote process results, current-revision CI, configured review, and merge-group acceptance remain pending.
Actual process interruption and complete native acceptance remain unmeasured by this shared package.
Documentation was inspected as source.
Rendered usability and complete language conformance remain unverified.

## Ownership

The shared orchestration belongs to assignment 1 of `Encoder20261125`.
The shared pipeline owner coordinates its delivery PR and owning-register reconciliation.
The SOLIDWORKS and Fusion adapters retain separate format owners and acceptance evidence.
Dependencies are the existing research launcher, SDK readers, deterministic candidate adapters, and independently measured native receipts.
The bounded exit requires revision-bound shared process evidence and the applicable PR gates.
Full format acceptance retains the criteria above.
