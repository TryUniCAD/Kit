# Bulk decoded JSON comparison

## Behavior

`re/automation/CompareDecoded.py` compares existing codec `CadDocument` JSON in bulk.
It runs independently of the SOLIDWORKS and Fusion decoders.
It reuses the bounded typed graph engine instead of introducing feature-specific comparison scripts.

Directory mode pairs identical relative paths and records missing counterparts.
Manifest mode accepts explicitly paired, independently named exports.
Feature correspondence remains independent of names and native identifiers.
Each pair receives a detailed JSON report.
The completed batch publishes a readable summary and a final machine-readable summary.
Available input hashes, report hashes, explicit geometry units, tolerance choices, and implementation hashes remain recorded.

Invalid inputs remain explicit outcomes without hiding later pairs.
Ambiguity, unresolved source evidence, and exhausted comparison budgets cannot produce equality.
Unresolved source issues also require exit `3` when the engine's primary status records observed differences.
Engine report-budget refusals remain incomplete observations instead of input errors.
Output publication refuses existing destinations.

## Usage and limits

Follow [the bulk comparison procedure](../../../../Tasks/CompareDecodedDocuments.md).
Geometry units are mandatory; absolute tolerances default to zero.
The programme accepts at most 1000 pairs and 32 MiB per document.
The output budget is 1 GiB.
The existing comparator's unsupported-domain and qualification boundaries remain unchanged.
Native acceptance and independent semantic qualification are not established.

## Verification

Process integration coverage invokes the actual command against codec-serialized documents.
It covers renamed identities, mixed outcomes, unit normalization, manifest validation, ambiguity, work budgets, sidecar selection, and overwrite refusal.
The real-export case consumes the committed Fusion and SOLIDWORKS feature-ladder JSON through the same process boundary.
Mixed-error cases retain later unresolved reports while requiring input-error exit precedence.
Missing-counterpart cases retain available file fingerprints without treating incomplete pairs as decoded documents.
Directory discovery streams entries within its fixed discovery budget instead of first materializing each directory.
Typed-reference cases cover feature output bodies, cut targets and face-offset operands, preserving collection order and refusing dangling identities.
The [exact unit-factor correction](ExactTopologyUnitFactors.md) adds zero-tolerance topology scaling controls.
The tests use the existing complete-suite collection, merge-queue planner, shards, and report.
No new workflow or CI job is introduced.
Local test execution has not been performed.
Scoped Black, Prettier, Python steering, Pyright, tracked-path policy, and Python 3.11 syntax checks passed before publication.
Remote process execution, current-head CI, configured review, and queue acceptance remain pending.
Documentation has been inspected as source; rendered usability and complete language conformance remain unverified.

## Ownership

Task `A06g-BulkDecodedComparison` is owned by Codex on `codex/bulk-semantic-comparison`.
Delivery is [PR #273](https://github.com/TryUniCAD/Kit/pull/273).
It depends on the existing A06a graph comparator and interchange codec.
The [automation register](../../../../Reference/Research/AutomationSteps.md#a06g-bulkdecodedcomparison-standalone-bulk-command) records its delivery and exit condition.
This delivery does not complete A06b or change the production conversion boundary.
