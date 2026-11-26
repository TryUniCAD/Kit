# Run deterministic research with Kit

## Purpose

Run PR #94's pinned readers, corpus, durable controller, and configured supervisor through the installed `kit` command.
The CLI delegates to existing implementations and preserves their evidence contracts.
Users do not write Python imports or scripts.

For multiple local instances, use the [shared research queue](../Reference/Research/SharedResearchQueue.md)
to submit revisioned requests to one controller and supervisor.
Existing private catalogue runs retain their own stores unless their jobs are explicitly submitted through that endpoint.

## Before you start

Install a CLI revision from its source checkout with `uv tool install .`.
Use `uv tool install --python 3.14 .` when Fusion research is required.
The launcher uses the interpreter running `kit` and does not silently select another environment.
The equivalent module command is `python -m KitCli research`.
`python -m convert research` reports an error directing callers to these developer entry points.

Use `kit decode` for the installed production reader. `kit run --input` launches a discovery experiment in the research workspace of the selected checkout. See [SOLIDWORKS dimension provenance](../Changes/Research/Inference/SolidWorksDimensionProvenance.md) for how to interpret its strict decode.

Select a trusted checkout containing PR #94 and the corpus's pinned Git objects.
`--root` authorizes execution of that checkout's research code and SDK.
The wheel contains the SDK and CLI, not research fixtures or the `re/` workspace.
On Windows, the supervisor requires Windows 10 or newer, Python 3.14 or newer, and the locked `pywin32` development extra.
The selected checkout must advertise Windows CLI shutdown protocol 1.
An older or incompatible checkout is rejected before worker dispatch; update the selected `--root` checkout when prompted.
On Windows, reader, corpus, and controller commands wait for completion and return the tool's exit status.

The examples use `/path/to/KitPr94` for the trusted research checkout.
Replace it with its absolute path; the installed CLI checkout can be different.
Replace example output paths with unused directories that you own.
Preserve the original CAD files.

## Compare decoded JSON exports

From a trusted checkout with the comparison command, run:

```sh
kit research --root . compare SolidWorks Fusion --unit mm -o NewComparison
kit research --root . compare --manifest /path/to/Pairs.json --unit mm -o /path/to/NewComparison
```

`SolidWorks` and `Fusion` are folders of decoded JSON. Files pair by matching relative paths.
Either folder can go first. The first is labeled left in reports and the second is labeled right.
Choose a new output directory for each run.
Declare the actual geometry units. Use `--left-unit` and `--right-unit` instead of `--unit` when the sides differ.
The command reads existing decoded JSON and reports every pair.
It copies the first folder's original JSON to `NewComparison/unified/` for each pair that compares equal at zero tolerance with no unresolved issues.
See the [comparison procedure](CompareDecodedDocuments.md) for pairing rules, reports and exit codes.

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

For several SOLIDWORKS parts, use a checkout with batch support.
Add `--batch` and repeat `--asset` for up to 1000 distinct pinned parts.

```sh
kit research --offline --root /path/to/KitPr94 solidworks --batch \
  --asset re/solidworks/examples/.SLDPRT/example.SLDPRT \
  --asset "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/CUBIERTA.SLDPRT" \
  --output /tmp/KitPinnedSwBatch
```

Batch `summary.json` lists the paths and their document directories in request order.
Keep each directory's `document.json` and `receipt.json` together.
One `--configuration` value applies to every part.
A failed pin or decode returns status `1` and publishes no batch.
The batch can write up to 4 GiB of documents and receipts.
Use fewer assets if the run exceeds this limit.
Omit `--offline` to request native verification for the complete batch.
Use `--batch` every time you intend to decode several SOLIDWORKS assets.
See [legacy SOLIDWORKS asset selection](../Gotchas/Research/Offline/LegacySolidWorksAssetSelection.md).

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

The [blind-boss audit](../Changes/Research/Solidworks/BlindBossDecodeAudit.md) records an executed offline scope and its limits.
Offline readers decode existing native files without launching CAD applications.
Archived application measurements support replay checks, not fresh vendor acceptance.
The run saves decoded documents and receipts without committing files or promoting production support.
Use the [codec patch procedure](#export-a-qualified-codec-change) to propose a corroborated reader change.

The installed CLI automatically requests native API verification after decoding.
Use `kit research --offline --root /path/to/KitPr94 solidworks ...` for offline decoding.
The offline option also supports Fusion and must precede the tool name.
Offline runs preserve reader exit codes and artifacts without contacting a native API.
Native verification remains pending, and vendor acceptance is not established.
Read `NativeVerification.json` for the application observations and case comparisons.
An unavailable API returns status `4` with instructions for the local machine.
Failed or invalid native verification returns status `5`.
Fusion decoding failures retain status `3`.
The original decoding artifacts remain available after a verification failure.
Older trusted checkouts also retain their decoding artifacts when they lack native verification support.
The launcher reports that verification was not performed and returns status `4` after successful legacy decoding.

For SOLIDWORKS, use Windows with its licensed registered COM API and `pywin32` in Kit's Python environment.
For Fusion, run `kit research --root /path/to/KitPr94 api enable fusion`.
Run KitVerify once and select **Run on Startup** in Fusion **Scripts and Add-Ins**, then close Fusion.
Kit starts fresh verification sessions automatically.
Close existing vendor sessions before verification.
See [automatic native reader verification](../Changes/Research/Automation/AutomaticNativeReaderVerification.md) for checks, scope, and current limitations.

## Manage durable research jobs

The corpus and controller retain their existing commands:

```sh
kit research --root /path/to/KitPr94 corpus check --manifest /path/to/KitPr94/re/automation/Corpus.json
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState init --max-running 4
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState status
```

Use `controller --help` for evidence binding, batch submission, claims, lease renewal, and result submission.
The CLI preserves stale-lease status `3` and the controller's integrity checks.

The attribution migration preserves the original capture lineage contract and Fusion outcome baseline.
Capture intake reports the original and current input identities plus the four reviewed text migrations.
Other content, mode, roster, or native-asset changes still fail validation.
The Fusion census reports its historical and current manifest hashes separately.
Only the documented metadata-only hash pair is accepted across that migration.
See [attribution queue repairs](../Changes/Ci/AttributionQueueRepair.md).

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
On Windows, the supervisor launcher creates a separate console process group.
It forwards handled interrupt, termination, and break signals as `CTRL_BREAK_EVENT`, then waits for supervisor cleanup and preserves its exit status.
The supervisor handles that event through its normal shutdown and worker settlement path.
Console-event forwarding requires the launcher and supervisor to share a Windows console.
Ordinary Windows reader and controller commands retain their existing wait-for-completion behavior.
An uncatchable launcher kill cannot be forwarded; use the existing research lease and recovery controls after forced termination.
Supervisor contention retains status `4`.

No production decode runner or model-provider registry is supplied by this bridge.
Models remain disabled by default.
To request GPT-6.2-Sol advice automatically on inference stalls, add `--codex-on-stall` to the supervisor's `run` command. See [automatic decoder advice](../Changes/Research/Advice/AutomaticDecoderAdvice.md).

The separate [Codex advice command](../Changes/Research/Advice/CodexFallback.md) can watch an approved parked inference job.
It uses the local Codex login and writes proposals for independent verification.
Application workers remain separate isolated research oracles.
See [session output lifetime](../Gotchas/Research/SupervisorSessionOutputLifetime.md) before implementing a persistent decode runner.

## Identify an input by content

Run `kit run --root . auto --input /path/to/unknown --directory /tmp/KitUnknownRun`. The [content-driven input mode](../Changes/Research/Inference/IdentifyResearchInput.md) accepts an extensionless file, probes for native Fusion and SOLIDWORKS containers, and inspects standalone ASM geometry.

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
With `--input`, a [file-level stall](../Changes/Research/Inference/FileStallExperiments.md) can use one advice call even when the catalogue has no parked worker job. The remaining call budget is available to the workers. See `FileExperiments.json` for local control replays when an applicable experiment exists.

Omit `--advisor` to run deterministic research alone. Advice requires macOS or Linux.
Use `--advice-calls N` to set the limit for the batch. The default is four calls.

Kit reserves 4096 MiB of available memory for the system during the offline stage by default.
Use `--reserved-memory-mib 1024` to reserve 1 GiB, or `--reserved-memory-mib 0` for zero reserve.
An explicit value applies to every supervisor stage started by this batch.
Kit still requires enough available memory for each worker's estimated demand.

Kit runs mapped scopes sequentially in prerequisite order.
Each scope's assessment depends on all jobs from the preceding scope.
Kit automatically runs independent offline jobs within a scope in parallel when memory and CPU are available.
Small compatible rescans can share one worker process in groups of up to four files.
Each file retains its own result and receipt.
Use `--workers N` to cap the number of offline workers.
Set `--workers 1` for a serial offline run. Native capture workers follow their own supervisor configuration.

With a configured native worker, a reviewed capture can start while independent offline jobs run.
The capture still needs its prerequisite assessment and a licensed application session.
Once the application owner has prepared its worker, use `--native-ready` to allow dispatch.
See the [catalogue native handoff](../Changes/Research/Controller/DeterministicInference.md#run-both-complete-catalogue-inventories).

Kit shows active workers, queued jobs, and waits in the terminal while it runs.
Progress uses standard error. The final JSON remains on standard output.
Read `CatalogueResult.json` for completed and blocked entries. Exit status 2 means coverage remains incomplete.
The catalogue also batches completed rescan inputs through the locally available vendor API.
Read its `native_verification` field and the separate application reports.
Missing API access prevents the whole catalogue from reporting completion.
Read `State/decoder-advice/<receipt>/Advice.json` for suggestions produced during the offline batch stage.
A suggestion requires an independently checked experiment before it can become a decoder rule.
Use `kit run --root . fusion --help` for all options.

To pause a run, open another terminal and use its existing output directory.
Let the active workers finish before you resume.

```sh
kit run --root . fusion --directory /tmp/KitFusion --pause
kit run --root . fusion --directory /tmp/KitFusion --resume
```

Resume from the same source revision. Kit reuses the original catalogue and worker settings.
To retry a parked native job after its owner restores the application, add `--native-ready` to `--resume`.

## Keep the interfaces distinct

### Author new catalogue samples

Add `--author-samples` to a catalogue run to create new native samples before
decoding them. `--authoring-cases` selects catalogue identities and validated
parameter overrides. `--prepare-only` writes the plan without launching CAD.
Discovery uses P01, P03, P04, and the five registered extrusion recipes.
Use `--capture-mode qualification` for P02. Use `--capture-mode holdout` for P05
and the four registered revolution recipes.

Add `--authoring-grid three-values` to vary each exposed parameter independently
across three legal values. Omit it to retain baseline cases. New SOLIDWORKS
recipes share native batches of at most three cases, with separate decoder jobs.
Native execution requires a Windows desktop context outside AppContainer.
Native outputs persist under the run's `NativeAttempts` directory.
See [reusable recipe builders](../Changes/Research/Supervisor/Catalogue/ReusableRecipeBuilders.md)
for exact identities, limits, and evidence requirements.
The [thin-wall side check](../Changes/Research/Supervisor/Catalogue/SolidWorksThinWallSide.md)
covers the written thin-extrude recipe's native mode, bounds, and reopen.

SOLIDWORKS needs `--solidworks-host` with installed executable and interop paths.
Fusion needs its native worker options and `--fusion-lifecycle` for automatic
owned restart. Use the same source revision across workers and the selected
checkout. Pause/resume keeps the existing native and decoder receipts.

See [catalogue sample authoring](../Changes/Research/Supervisor/Catalogue/CatalogueSampleAuthoring.md)
for the case format, native host requirements, limitations, and evidence rules.

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

| Symptom                              | Action and stop condition                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Missing research script              | Select the intended trusted PR #94 checkout                                                    |
| Missing pinned Git object            | Fetch the manifest's committed revision before retrying                                        |
| Hash or prefix mismatch              | Restore or review the intended pin; do not relax checks                                        |
| Existing output directory            | Choose an unused path; no overwrite bypass is exposed                                          |
| Fusion requires Python 3.14          | Install or run the CLI with that interpreter                                                   |
| Windows supervisor checkout rejected | Use a trusted checkout with Windows CLI shutdown protocol 1 and the Windows dependencies above |
| Runner unavailable                   | Configure an implemented runner or retain the blocked prerequisite                             |

Tests execute only in remote CI.
The Linux and Windows [compatibility jobs](../Changes/Commands/ResearchCandidateCompatibility.md) install the CLI from the workflow candidate and select a separate research checkout at the same revision.
See [the change record](../Changes/Research/DeterministicResearchCli.md) for compatibility coverage and limits.

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

The [sketch count integration checks](../Changes/Research/Inference/Validation/SketchCountReviewCoverage.md) cover unitless export and exclude count-based distance constraints.

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

For standalone spheres and tori, see [analytic solid reader generation](../Changes/Research/Inference/AnalyticSolidReaderGeneration.md) for the generated script, its required Python paths and the native comparisons that gate the patch.

For standalone planar shells and geometry journals, [planar journal replay](../Changes/Research/Inference/PlanarJournalReplay.md) describes state reconstruction and comparison with a measured snapshot.

For an extracted native configuration stream, use [raw scalar reader inference](../Changes/Research/Inference/RawScalarReaderInference.md) to fit a numeric layout to discovery measurements and replay it on another raw stream with `--control`.

Use [scalar feature associations](../Changes/Research/Inference/ScalarFeatureAssociations.md) to distinguish measured feature names from candidates that depend on the preceding serialized marker.

Use a single-parameter edit to [compare generated scalar readings across two native parts](../Changes/Research/Inference/PairedScalarChanges.md).

For known native captures, the single-input command [selects measured controls automatically](../Changes/Research/Inference/AutomaticScalarControls.md).

For an unrecognized ZIP package, inspect [member structure and cross-file references](../Changes/Research/Inference/UnknownArchiveMembers.md).

[Native FreeCAD input](../Changes/Research/Inference/FreeCad/FreeCadFileResearch.md) also runs the neutral feature reader and compares matching recorded controls.

See [edited native extrusion depths](../Changes/Research/Inference/FreeCad/FreeCadDepthEdits.md) when the embedded model is stale.

[Edited prism evidence](../Changes/Research/Inference/FreeCad/EditedPrismEvidence.md) compares the predicted solid with its saved shape member.

[Edited extrusion graph recovery](../Changes/Research/Inference/FreeCad/EditedExtrusionGraph.md) records the candidate feature definition and its driving parameter.

The generated reader and graph receipt retain the same input identity in `source_sha256`; see [queue reader repairs](../Changes/Research/Inference/Validation/QueueReaderRuntimeRepairs.md).

[Derived extrusion readers](../Changes/Research/Inference/FreeCad/DerivedDepthGraphReader.md) capture replayed native-to-graph bindings in Reader.patch.

[Complementary depth discovery](../Changes/Research/Inference/FreeCad/ComplementaryDepthBindings.md) explains the extra controlled variations and independent replays.

[SolidWorks scalar display precision](../Changes/Research/Inference/SolidWorksScalarPrecision.md) covers rounded declarations and diameter and radius dimensions.

[Native scalar record roles](../Changes/Research/Inference/ScalarRecordRoles.md) distinguish driving records, display values and unclassified trailers.

[Pattern count encoding evidence](../Changes/Research/Inference/NamedPatternCountEvidence.md) records competing interpretations at named scalar offsets.

[Counted text discovery](../Changes/Research/Inference/CountedTextDiscovery.md) generates a prefix reader for related raw streams.

[Resuming text decoding after a gap](../Changes/Research/Inference/ManifestTextGaps.md) describes the bounded search and held-out replay.

[Executable text-gap experiments](../Changes/Research/Inference/AdvisorTextExperiment.md) explain how an advisor choice advances a stalled raw stream.

Catalogue finalization verifies completed scope inputs after the supervisor settles, even when later scopes still await evidence.
Paused runs do not start a native batch.
Later scopes remain dependent on every predecessor job; a memory reserve can therefore leave the first scope queued and later scopes waiting for evidence.
See [native verification queue repairs](../Changes/Research/Automation/NativeVerificationQueueRepairs.md) for file-boundary behavior and verification evidence.

## Related information

- [Queue Fusion diagnostic repairs](../Changes/Research/Inference/Validation/QueueFusionDiagnosticRepairs.md)
- [Fusion vocabulary refusal stages](../Gotchas/Research/Readers/FusionVocabularyRefusalStage.md)
- [General CLI](CommandLine.md)
- [Research plan](../Reference/Research/AutomationPlan.md)
- [Step register](../Reference/Research/AutomationSteps.md)
- [SOLIDWORKS reader](../Reference/Research/SolidworksResearchReader.md)
- [Fusion reader](../Reference/Research/FusionResearchReader.md)

## Export a qualified codec change

Supply a reviewed format rule, a completed scope and at least two tracked files with independently measured semantic values. Pin the checkout to the request's full Git revision. Use a trusted local Docker image with Python 3.14 and any dependencies the selected adapter requires. Pass its immutable image ID (from `docker image inspect --format '{{.Id}}' IMAGE`).

```sh
kit run --root . fusion --catalogue Catalog.sqlite --directory Run \
  --codec-request request.json --codec-image "$IMAGE_ID" --codec-output reader.patch
```

To use a settled run, take the assessment job ID and receipt digest from the scope's jobs in `Run/CatalogueResult.json`.

```sh
kit research --root . codec-patch --store Run/Store --job "$JOB" --receipt "$RECEIPT" \
  --request request.json --image "$IMAGE_ID" --output reader.patch
git apply --check --index reader.patch
git apply --index reader.patch
```

A request contains these fields.

| Field                                     | Required value                                                                                                                                                |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`, `base`, `scope`                   | PascalCase patch name of 4–19 letters, full Git commit and exact scheduled scope                                                                              |
| `reference`, `rule`                       | Tracked research Markdown path under `re/` and a written interpretation of the corroborated finding                                                           |
| `modules`                                 | Explicit Python source paths under `src/convert/adapters/` or `src/convert/Formats/`                                                                          |
| `contract.mode`, `contract.target_suffix` | `reader` with an empty suffix, or `writer` with the output extension                                                                                          |
| `contract.cases`                          | Two to sixteen objects with tracked `file`, its `sha256`, and an `expect` mapping from decoded document JSON pointers to independently measured scalar values |

For example, an expected value for the first circle sketch entity can be expressed as `{"/document/sketches/$tuple/0/entities/$tuple/0/geometry/$type":"CircleGeometry"}`. Each case must also check a feature-history value and a parameter value. For a writer, measure the same field on at least two controls with different expected values so a constant output cannot pass both. Select measurements specific to the proposed change. The exporter runs the repository recorded-payload scanner before qualifying a candidate.

When the baseline fails a measurement, Codex receives the selected modules, the reviewed rule and the finding. The default is GPT-6.2-Sol at medium reasoning effort. Keep proprietary contents out of the written rule. Supply `--candidate replacements.json` (or `--codec-candidate` during a catalogue run) to qualify a mapping from each selected path to its complete proposed source without a model call.

Qualification runs each case through the public CLI in a network-isolated container. Writer cases reopen the generated file with the reader from the pinned base. The resulting Git patch includes codec changes, a replayable regression, the pinned cases and a change entry. Review the patch for generalization and donor data. Native application reopen, editing and losslessness still require the format's acceptance controls.

## Recorded native feature ladders

The [2026 feature ladder package](../../re/FeatureLadders2026/README.md) retains native inputs, strict outcomes, and typed-native inspection reports.
Its manifest includes failed and blocked cases. These research outcomes do not qualify conversion or complete semantic recovery.

## Verify the selected launcher

Another installation can shadow the executable installed with Python 3.14.
Resolve `kit` before resuming a durable native campaign and inspect its entry-point interpreter.
Use the verified installation's absolute path if necessary.
The [shadowed launcher gotcha](../Gotchas/Research/Supervisor/Runtime/ShadowedKitLauncher.md) records the observed supervisor failure and safe repair.

## Circular rim fillet qualification pack

The [rim-fillet pack](../../re/Fusion/RimFilletPack/README.md) separates source-free writer acceptance, typed reconstruction and public conversion refusals.
Replay uses existing codecs without a CAD runtime. Native measurements remain revision-bound research evidence.
