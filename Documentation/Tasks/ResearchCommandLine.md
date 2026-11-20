# Run deterministic research with Kit

## Purpose

Run PR #94's pinned readers, corpus, durable controller, and configured supervisor through the installed `kit` command.
The CLI delegates to existing implementations and preserves their evidence contracts.
Users do not write Python imports or scripts.

## Before you start

Install a CLI revision from its source checkout with `uv tool install .`.
Use `uv tool install --python 3.14 .` when Fusion research is required.
The launcher uses the interpreter running `kit` and does not silently select another environment.
The equivalent module command is `python -m KitCli research`.
`python -m convert research` reports an error directing callers to these developer entry points.

Select a trusted checkout containing PR #94 and the corpus's pinned Git objects.
`--root` authorizes execution of that checkout's research code and SDK.
The wheel contains the SDK and CLI, not research fixtures or the `re/` workspace.
The supervisor requires Linux or macOS.
On Windows, reader, corpus, and controller commands wait for completion and return the tool's exit status.

The examples use `/path/to/KitPr94` for the trusted research checkout.
Replace it with its absolute path; the installed CLI checkout can be different.
Replace example output paths with unused directories that you own.
Preserve the original CAD files.

## Decode committed inputs

Decode a pinned SOLIDWORKS part:

```sh
kit research --root /path/to/KitPr94 solidworks --asset re/solidworks/examples/.SLDPRT/example.SLDPRT --output /tmp/KitPinnedPart
```

Inspect `receipt.json` before using `document.json`.
Retain both files for subsequent research.
The reader selects committed Git bytes and verifies path, blob, size, SHA-256, and prefix.
The document remains unchanged SDK `CadDocument` serialization.
Research documents carry `kit.research_read_status: unqualified` in their existing metadata field.
The CLI refuses conversion of those marked documents, including marked nested components, before staging output.
Keep the marker and receipt; the CLI does not promote research results into qualified conversion inputs.
The separate receipt binds source, SDK, tools, options, hashes, and unresolved evidence.

For Fusion, use Python 3.14 and select one or more committed assets:

```sh
kit research --root /path/to/KitPr94 fusion --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitPinnedFusion
```

Repeat `--asset` for up to 1000 distinct inputs.
Fusion publishes `summary.json` and separate document/receipt directories for decoded assets.
Exit status `3` means a published run contains rejected or reader-error outcomes.
Inspect every outcome before interpreting the batch.

Use `--manifest PATH` for another supported manifest.
SOLIDWORKS also accepts `--configuration NAME`.
Fusion `--allow-partial` means strict-first decoding with explicit fallback, unlike inspection's forced `--partial` reader mode.
Set `--root` once before the tool name; forwarded root overrides and their abbreviations are rejected.
Use `kit research --root /path/to/KitPr94 fusion --help` for the authoritative reader help.

Expected result: the existing reader publishes its normal artifacts or reports its existing failure.
Successful receipts do not establish portable completeness or native conversion acceptance.

## Manage durable research jobs

The corpus and controller retain their existing commands:

```sh
kit research --root /path/to/KitPr94 corpus check --manifest /path/to/KitPr94/re/automation/Corpus.json
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState init --max-running 4
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState status
```

Use `controller --help` for evidence binding, batch submission, claims, lease renewal, and result submission.
The CLI preserves stale-lease status `3` and the controller's integrity checks.

## Run configured sessions

Prepare an actual runner registry and `Supervisor.json` with the [supervisor guide](../Reference/Research/ResearchSupervisor.md).
Use only trusted configuration and runner programs.

```sh
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json submit Batch.json
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json run --idle-seconds 30
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json status
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json pause decode --reason "operator hold"
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json resume decode
```

The supervisor owns pools, claims, leases, retries, restart fencing, and configured worker dispatch.
On Linux and macOS the CLI starts a separate research session and owns signal handling before spawning it.
Interrupt, termination, hangup, quit, and user signals are forwarded; terminal suspension stops both launcher and child, and continuation resumes the child.
Startup signals wait for the child reference, and continuation cancels a queued suspension.
It waits for cleanup, preserves output and exit statuses, and terminates with the child's signal when that child is killed.
An uncatchable launcher kill cannot be forwarded; use the existing research lease and recovery controls after forced termination.
Supervisor contention retains status `4`.

No production decode runner or model-provider registry is supplied by this bridge.
Models remain disabled by default.
To request GPT-6.2-Sol advice automatically on inference stalls, add `--codex-on-stall` to the supervisor's `run` command. See [automatic decoder advice](../Changes/Research/Advice/AutomaticDecoderAdvice.md).

The separate [Codex advice command](../Changes/Research/Advice/CodexFallback.md) can watch an approved parked inference job.
It uses the local Codex login and writes proposals for independent verification.
Application workers remain separate isolated research oracles.
See [session output lifetime](../Gotchas/Research/SupervisorSessionOutputLifetime.md) before implementing a persistent decode runner.

## Run a CAD catalogue with optional advice

Use a clean checkout with the catalogue runner and install Kit from that revision with
`uv tool install --python 3.14 .`. Obtain [Fusion Catalog.sqlite](https://github.com/TryUniCAD/Kit/pull/163)
or [SOLIDWORKS FeaturePlan.json](https://github.com/TryUniCAD/Kit/pull/164).
Choose an unused output directory outside the checkout.

```sh
kit run --root . fusion --catalogue /path/to/Catalog.sqlite --directory /tmp/KitFusionRun --advisor codex
kit run --root . solidworks --catalogue /path/to/FeaturePlan.json --directory /tmp/KitSolidworksRun --advisor codex
```

| Options                                       | What runs                                                                        |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| `--advisor codex --auth login`                | Installed Codex CLI with saved sign-in. Run `codex login` first if needed.       |
| `--advisor claude --auth login`               | Installed Claude Code CLI with saved sign-in. Sign in through Claude Code first. |
| `--advisor codex --auth api`                  | Installed Codex CLI with `CODEX_API_KEY` or `OPENAI_API_KEY`.                    |
| `--advisor claude --auth api`                 | Installed Claude Code CLI with `ANTHROPIC_API_KEY`.                              |
| `--advisor ollama --auth local --model MODEL` | Ollama at `127.0.0.1:11434` with an installed local model.                       |

Cloud providers default to login mode. Integrated Codex advice uses `gpt-6.2-sol` with medium reasoning. Use `--model` to override the model. The Claude CLI selects its configured model when no override is given.
For Ollama, start the server with `OLLAMA_NO_CLOUD=1` and supply an installed model tag.
Omit `--advisor` to run deterministic research alone. Advice requires macOS or Linux.
Use `--advice-calls N` to set the limit for the batch. The default is four calls.

Kit reserves 4096 MiB of available memory for the system during the offline stage by default.
Use `--reserved-memory-mib 1024` to reserve 1 GiB, or `--reserved-memory-mib 0` for zero reserve.
An explicit value applies to every supervisor stage started by this batch.
Kit still requires enough available memory for each worker's estimated demand.

Kit automatically runs independent offline jobs in parallel when memory and CPU are available.
Use `--workers N` to cap the number of offline workers.
Set `--workers 1` for a serial offline run. Native CAD workers follow their own supervisor configuration.

With a configured native worker, a reviewed capture can start while independent offline jobs run.
The capture still needs its prerequisite assessment and a licensed application session.
Once the application owner has prepared its worker, use `--native-ready` to allow dispatch.
See the [catalogue native handoff](../Changes/Research/Controller/DeterministicInference.md#run-both-complete-catalogue-inventories).

Read `CatalogueResult.json` for completed and blocked entries. Exit status 2 means coverage remains incomplete.
Read `State/decoder-advice/<receipt>/Advice.json` for suggestions produced during the offline batch stage.
A suggestion requires an independently checked experiment before it can become a decoder rule.
Use `kit run --root . fusion --help` for all options.

## Keep the interfaces distinct

| Command                                       | Contract                                                   |
| --------------------------------------------- | ---------------------------------------------------------- |
| `kit convert SOURCE DESTINATION`              | User conversion through the SDK and its output policy      |
| `kit decode SOURCE`                           | Working-file inspection with a `kit.decode` report         |
| `kit research --root CHECKOUT solidworks ...` | Pinned input, unchanged neutral document, separate receipt |
| `kit research --root CHECKOUT fusion ...`     | Pinned batch, per-asset receipts, run summary              |
| `kit research --root CHECKOUT supervisor ...` | Existing configured runner sessions and controller state   |

The research checkout can differ from the installed CLI checkout.
The selected script starts in a fresh interpreter and explicitly loads its own SDK source.
The CLI forwards reader output and exit codes without reconstructing fingerprints or receipts.
It executes no shell and imports no research modules into production conversion.
The packaged `KitCli` developer composition lives in `Cli/`, separately from the two SDK packages in `src/`.
Conversion and inspection do not import its process launcher dependencies.

## If the command fails

| Symptom                           | Action and stop condition                                          |
| --------------------------------- | ------------------------------------------------------------------ |
| Missing research script           | Select the intended trusted PR #94 checkout                        |
| Missing pinned Git object         | Fetch the manifest's committed revision before retrying            |
| Hash or prefix mismatch           | Restore or review the intended pin; do not relax checks            |
| Existing output directory         | Choose an unused path; no overwrite bypass is exposed              |
| Fusion requires Python 3.14       | Install or run the CLI with that interpreter                       |
| Supervisor unavailable on Windows | Use Linux or macOS for orchestration                               |
| Runner unavailable                | Configure an implemented runner or retain the blocked prerequisite |

Tests execute only in remote CI.
The Linux and Windows [compatibility jobs](../Changes/Commands/ResearchCandidateCompatibility.md) install the CLI from the workflow candidate and select a separate research checkout at the same revision.
See [the change record](../Changes/Research/DeterministicResearchCli.md) for compatibility coverage and limits.

## Related information

- [General CLI](CommandLine.md)
- [Research plan](../Reference/Research/AutomationPlan.md)
- [Step register](../Reference/Research/AutomationSteps.md)
- [SOLIDWORKS reader](../Reference/Research/SolidworksResearchReader.md)
- [Fusion reader](../Reference/Research/FusionResearchReader.md)

## Start research from a CAD file

```sh
kit run --root . fusion --input part.f3d --directory /tmp/KitPartRun --advisor codex
```

Use `solidworks` for a part or assembly from SOLIDWORKS. The runner snapshots up to 128 MiB of input, inventories its streams, attempts a strict neutral decode, and uses the partial reader if strict decoding refuses the file.

The run saves the successful decode layers and a `FileScope.json` report containing the input digest, reader refusals, features without mapped experiments and stream intervals without cited provenance. Intervals are zero-based and end-exclusive within each uncompressed stream. A cited range can still contain unresolved fields.

Typed blind-boss and through-all cut records select the existing P03 and P04 research experiments. The experiments use their controlled corpus. Their receipts can inform the investigation of the input. File-driven runs report incomplete coverage until independent evidence establishes whole-file semantics.

If strict Fusion decoding stops at an unknown class, the run locates the exact segment and object in the native report, checks its class GUID, and follows typed local and cross-segment references until no new reachable objects remain. `Input-references.json` records each field and its target, including missing targets. Cycles and repeated references preserve their edges.

For a Fusion variant present in a measured paired capture, the run also decodes both baseline saves. It verifies their digests and compares aligned numeric and Boolean fields by segment, object, class and field. `Input-repeat-save.json` identifies repeat-stable fields that differ in the input. Their functional interpretation still requires distinguishing controls.

When a design graph class identity is missing, the runner checks the saved segment version and base class against its decoded wire schema, runtime reflection and recorded class vocabulary. On agreement it adds one binding in a temporary copy of the reader, reruns strict decoding and examines the next refusal. It tries at most 32 bindings. A progressing run writes `DesignNames.patch` and `Input-design-names.json`. Review the source revision and evidence before applying the patch with `git apply --check --index DesignNames.patch`.

For models outside the single-extrusion projection, `Input-timeline.json` follows each component's saved feature order. Where measured evidence is available, it compares the recovered fields to an independent capture. Paired captures can also yield `Input-body-measurements.json`. A unique single body can be measured even when its decoded display name disagrees. Other Fusion studies are looked up by the input digest in tracked ground-truth records. The report identifies whether a measurement came from a reopen or from the live feature before export.

For Fusion inputs, inspect `Input-body-correspondence.json` to identify individual bodies. When a tracked vendor capture matches the input's digest and size, the runner compares volume, surface area and centroid. It reports display names only when every body has exactly one independent match and those matches cover every captured body once. Each match includes the native user name, creation index and position in the saved body collection.

The correspondence report evaluates two predictions for each measured, unnamed body: the English prefix `Body` followed by its creation index or by its one-based position in the saved collection. It records counterexamples for each prediction. When both fit, it selects `RemoveFirstDefaultBody`. On a configured Fusion oracle, run `node re/Fusion/LocalOracle/RunLocked.mjs re/Fusion/LocalOracle/FeatureAuthoring/CaptureDefaultNames.py` to create that control. It removes the first of two independently extruded bodies and records the survivor's displayed name and geometry before export. Once the capture and export are tracked, run the decoder on the export to compare both predictions.

When the Fusion native model parses but its state encoder rejects a journal record, the runner examines the types produced by the installed reader. For missing frozen journal records with field-only declarations, it stages an explicit registry change, verifies native model equality after a complete semantic-state encode/decode cycle, then replays the native CLI in a fresh process. A successful run writes `BrepTypes.patch` and `Input-state-repair.json` and uses the recovered native report in the same investigation. Apply the patch only against its recorded base. This check establishes state serialization on the input file.

Body correspondence keeps historical body records in the inventory. A body missing from its recorded parent's complete, unambiguous collection is excluded from the current-body comparison only when no other decoded collection lists it.

Older captures sometimes omit centroid. When both inventories have exactly one current body, the runner can compare volume and area alone. Each accepted correspondence records the measurements it used. Multiple bodies still require all three centroid coordinates.

Every successfully parsed Fusion native model is eligible for timeline recovery. The report uses typed graph links to recover construction-plane and sketch names, and checks ordered names against a digest-matched captured timeline when available. A graph refusal is recorded in FileScope.json so the remaining analyses can finish.

The timeline report also follows each component's parameter table. For double parameters it checks the reciprocal binding, saved numeric value and owning timeline feature, and reports the name, expression, native value, display unit and role. Unsupported members retain a refusal. Captured parameter measurements are compared by unique name across the inventory.

For a named feature whose decoded label disagrees with a pinned vendor timeline, the runner searches its direct typed references for the measured user name. A unique field and target class must explain the mismatches for that feature class. A fresh reader process replays the proposed registry, checks every affected label and preserves other labels and feature order. A successful replay writes TimelineNames.patch. The patch contains field and class names only.

When a single feature owns the saved numeric parameters and the vendor inventory count differs, the runner can use up to eight other digest-pinned exports to infer which saved parameter roles appear in the vendor inventory. It uses the native feature family to locate controls and compares typed references, scalar modes and role sets. At least two matching controls must agree. The input export is held out, and its measured fields are used only to check the prediction. The timeline report preserves all stored parameters.

Parameter projection also uses fully exported study captures that measured the model parameter collection at the end of the timeline. The runner verifies the file digest, size, feature identity, parameter getter status and native context. If the input has no measurements, a prediction is reported separately from a held-out match.

On a SOLIDWORKS part with a decoded document and container, Input-dimension-evidence.json searches numeric encodings and displacements after a tagged dimension name in resolved feature streams. The runner trains on measured edits from other recipes and checks the input's named dimensions against actual stream bytes, neutral-reader spans and available vendor edit measurements. Missing or repeated names remain unresolved.

The dimension scan covers numbered configuration streams and their resolved-feature streams. After training, it scans the input directly for framed named dimension records, even when neutral projection fails. Each candidate retains its name, stream, byte offset and raw system value. Comparing named owners and spans requires a neutral document.

The SOLIDWORKS dimension report includes saved equations from numbered configuration streams. For a sum or difference of two named dimensions divided by a positive integer, it replays the expression using the recovered native values. Across sibling edit-and-restore measurements it tests both signs and divisors 1 through 16. The strongest result requires independent changes to each operand, a unique surviving operation, and agreement with a held-out export's vendor measurements and equation text.

Equation replay requires the configuration's relation-manager count to agree with the recovered list and the six-byte relation trailer to match. Numeric global literals include their explicit unit when present. These checks establish saved record framing, not vendor regeneration.

The file-driven run selects the existing P01 paired experiment when a sketch contains a single closed axis-aligned rectangular profile and at least two linked driving length constraints. FileScope.json records the sketch and driving parameter IDs used for dispatch.

For single-configuration SOLIDWORKS parts, the dimension report compares the keyword XML's feature IDs, dimension names and display values with the configuration's discovered binary records. Length comparisons use the file's recorded display precision. A match must identify one record which is also unique to that XML dimension. Other matches retain their ambiguity. This corroborates two representations inside one file.

For ambiguous keyword matches, the runner tests whether a dimension follows its owner's binary feature-name marker. It checks unambiguous dimensions first, groups the results by native feature kind, and excludes the target owner from supporting examples. A competing location stays ambiguous unless a single compatible marker interval survives. The proposed location remains a research hypothesis.

In SOLIDWORKS dimension evidence, inspect `keyword_evidence.dimensions[].integer_encoding_hypotheses` for alternative interpretations of unmatched displayed integers. Each entry records the stream, byte offset, and matching integer formats. These candidates do not count toward verified coverage.

For explicit SOLIDWORKS sketch pattern count classes, inspect `keyword_evidence.pattern_counts`. The decoder reads a named parameter and its linear or circular handle in the same saved feature interval, then compares their common count with the keyword dimension. The report includes both offsets and all compatible integer widths.

The pattern count reader searches the first 1,024 bytes of typed count handles in other saved parts for nine numeric encodings. Inspect `pattern_count_rule` for the intersection of matching offsets and encodings, the training file and stream hashes, and the held-out hashes. The decoder uses the surviving rule only when controls from multiple documents vary the count and cover both linear and circular patterns.

A strict SOLIDWORKS run can emit `SketchPatternCounts.patch` when it discovers a supported pattern family missing from the public reader registry. The command stages the candidate in temporary source, runs the public decode command, and checks the held-out count, integer type, empty unit, native span and every unrelated parameter. The accompanying `Input-pattern-count-reader.json` identifies the base commit and parameter IDs.

`keyword_evidence.feature_pattern_evidence` contains the training and held-out results for linear and circular feature pattern instance counts. A dimension with `pattern_count_reader_mismatch` has a decoded native count that still needs a corresponding public reader correction. A `verified_pattern_count` also agrees with the public parameter's unitless integer and exact scalar span.

For repeated SOLIDWORKS dimensions, inspect `keyword_evidence.extrusion_depth_evidence` for the training models, mirror locations and held-out predictions. Rows marked `paired_radial_dimension` identify the driving scalar, the separate display copy and the circle referenced by the neutral constraint.

For unresolved SOLIDWORKS features, inspect `discovered_feature_fields` in `Input-dimension-evidence.json`. The decoder searches for mirrored scalar fields for the input's own feature types and dimensions. A successful strict reader replay can produce `MirroredFields.patch` and `Input-mirrored-field-reader.json`.

For repeated SOLIDWORKS diameters, inspect the owning sketch, scalar offset, and measured center and rim in [sketch dimension evidence](../Changes/Research/Inference/SolidWorksProfileDimensionEvidence.md). Rounded angles can also report a verified mirror with its exact reader offset.

For dimensions with repeated values across different features, [owner anchors](../Changes/Research/Inference/SolidWorksOwnerAnchors.md) record the independently observed relationship used to select a source span.

When a SOLIDWORKS run generates multiple reader changes, apply the cumulative `Reader.patch` to its recorded base. The [successive reader passes](../Changes/Research/Inference/SuccessiveReaderPasses.md) report shows which parameters each pass verified.

A `paired_sketch_length` result records the driving and display offsets for a [full-precision sketch length](../Changes/Research/Inference/PairedSketchLengthPrecision.md).

For a `verified_native_radius` result, the [referenced circle dimension](../Changes/Research/Inference/ReferencedCircleDimension.md) entry explains how to inspect the saved center and rim.

The [revolution angle ownership](../Changes/Research/Inference/RevolutionAngleOwnership.md) report includes the axis ID, angle span, end specification and copy offsets for each verified revolution.

Use [local control parts](../Changes/Research/Inference/LocalControlParts.md) to supply a saved part with `--control`. Field-discovery passes use [registered discovery controls](../Changes/Research/Inference/DiscoveryControlEligibility.md). The dimension report records each supplied hash and its eligibility.

The [single-dimension control experiment](../Changes/Research/Inference/SingleDimensionControlExperiments.md) compares matching saves automatically. Inspect `next_control_edits` for the exact parameter and proposed native value when a distinguishing control is missing.
