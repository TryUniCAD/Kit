<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic inference and affected archive rescans

A07 searches structurally aligned byte spans for values from separately recorded
measurements. One assessment covers one native stream layout and semantic
quantity. Search candidates declare primitive type, byte order, units, scale
and offset. Optional powers and control factors express bounded derived
relationships. Integer comparisons are exact. Floating-point comparisons use
encoded patterns, representable neighbors and a NumPy scan of remaining offsets
within the declared quantity tolerance.

The runner freezes candidate locations and identities before it reads challenge
and holdout results. Challenge controls can refute a candidate. The runner
requires distinct declared lineage labels for holdout. An audited design and
native ancestry record establishes independence for qualification.
The report retains each candidate
span, source and stream digest, conflicting observation and unresolved control
axis. A matching candidate remains partial evidence pending loader and
application proof.

## Run an assessment

Use Python 3.14 with the locked development dependency group. Register
`inference.fields`, `inference.paired-gap` and `inference.rescan` with the supervisor. Use
`re/automation/InferenceRunner.py` followed by the whole-argument `{session}`
substitution as the runner. Generate its registry schema in the private state
directory.

```shell
uv run --frozen --group dev --python 3.14 python re/automation/InferenceRunner.py --schema
```

Bind the plan and each decoded stream through the [controller](../../../Reference/Research/ResearchController.md).
The plan contains `inference_version` set to 1, a `scope` label, a `quantity`
label, `encodings`, a nonnegative `tolerance`, `confounds` and
`observations`. Each observation identifies its `id`, independent
`lineage`, native archive `sha256`, `stream`, aligned byte `start` and
`length`, measured `value`, `controls`, bound input `role` and `split`.
The split is `discovery`, `challenge` or `holdout`. The plan's
`provenance.inputs` object is keyed by observation ID and contains the extracted
`archive_sha256`, `stream_sha256` and source evidence for each alignment.
The runner checks the archive identity and verifies the stream bytes against
the manifest pins.

Generate a controller schedule with `InferenceSchedule.py <request>`. Supply
`inference_version` set to 1, `scope`, `family`, `rule_version`,
`tool_version`, `plan_input`, `stream_inputs`, `archives`,
`distinguishing_evidence` and `depends_on`. The stream map binds each role
to a controller input. The archive map binds each native SHA-256 to a
`binding` and `format`. The supported rescan formats are `fusion.f3d`
and `solidworks.sldprt`. Submit the generated record with
`Controller.py --store <store> schedule <file>`.

To submit work ahead for multiple gaps, pass a `requests` array of these
records to the planner. Each request can include a `grids` array. Each grid
contains an A03 `job`, its `class` (`requested` or `standard`) and its
exclusive `installation` resource. The planner makes the assessment depend on
its requested grids. Requested grids take precedence at the next free
installation claim. The controller fills a target of ten queued grids per
installation from eligible supplied standard work, within store limits.
The scheduler rotates feature families within each lane and ranks jobs by open
dependents, distinct representative archives and distinguishing evidence.

### Dispatch a SOLIDWORKS catalogue feature

Read the existing [SOLIDWORKS planning catalogue](https://github.com/TryUniCAD/Kit/blob/f8cf67043e4f64c363dbe2add2128f1a58e99ab6/re/solidworks/PlannerCatalog/Sources/FeaturePlan.json).
Generate plans without a controller store. Keep the catalogue's SHA-256 from
the output or supply it with `--catalogue-sha256` to require that exact input.

```shell
python re/automation/InferenceGrid/FeatureDispatch.py --catalogue FeaturePlan.json manifest
python re/automation/InferenceGrid/FeatureDispatch.py --catalogue FeaturePlan.json \
  --feature family:extrude:boss-base-extrude plan
```

Plans have stable feature identities, dependencies, option axes, and recipe
readiness. An unmapped feature reports its missing recipe and pinned evidence.
The option axes identify research questions. They carry no claims about native
option combinations or qualification.

The P01 planar corner rectangle and its linear and driving dimensions share
one measured assessment and its twelve paired archive rescans. The P03
one-sided blind boss signed-depth assessment runs for each file format
separately. The P04 through-all body-selection assessment retains its two
affected archive rescans. Each route covers its stated discovery scope.
The circle and diameter entries also display their retained P02 native
readback evidence and the missing decoder route.

Use the same dispatch workflow with the
[Fusion planner inventory](https://github.com/TryUniCAD/Kit/tree/82259016c5d4ea92985b0dbff65d035edee0888d/re/Fusion/PlannerCatalog/Data)
by passing `--fusion-catalogue Catalog.sqlite`. The manifest reads Fusion's
feature API view and the reviewed two-point rectangle method from the same
database snapshot. It maps `api:adsk.fusion.ExtrudeFeature` to Fusion P03 and
`api:adsk.fusion.SketchLines.addTwoPointRectangle` to the shared P01 assessment.
The inventory's original qualification states stay visible.

### Run both complete catalogue inventories

From a clean checkout, use one command to prepare every catalogue entry,
submit all mapped scopes and run independent decoder jobs in parallel.
The supervisor chooses concurrency from available memory and CPU.
Use `--workers 1` for a serial run or a higher value as a ceiling.
Use a new output directory outside the source checkout.
You can supply either catalogue independently.

```shell
python re/automation/InferenceGrid/RunFeatureCatalogue.py \
  --solidworks-catalogue FeaturePlan.json --fusion-catalogue Catalog.sqlite \
  --directory /private/catalogue-run
```

The run saves `CataloguePlan.json`, each submission, the controller store,
and `CatalogueResult.json`. The plan has a row for every feature or API
entry. It submits a shared assessment once even if multiple rows use it.
An entry without a reviewed recipe is recorded as unavailable without
submitting decoder work. An entry with a
[written recipe](FeatureRecipeSpecs.md) but no captured native files is
recorded as `awaiting_capture`. Exit status 2 indicates incomplete coverage or
waiting evidence, and exit status 1 indicates a run failure.

For the P04 native evidence step on a configured Fusion host, supply
`--native-config`, `--native-kind` and `--native-resource`. That supervisor
configuration must use this run's `Store` directory.
The catalogue combines the offline and native pools in one local supervisor.
When the reviewed cut assessment records that it needs evidence, Kit queues the
native phases while independent offline jobs continue.
Use `--native-ready` only when the application owner has prepared its worker.
You can also set the resource available in the controller during the run.
The phases retain the standard Fusion owner restart procedure.
Read `PipelineSupervisor.log` and `NativeHandoffResult.json` for the handoff and worker status.

### Run one discovery scope

From a clean checkout, submit a mapped feature to an initialized A03 store
used by the inference supervisor. A mapped feature can also be selected
without a catalogue.

```shell
python re/automation/InferenceGrid/FeatureDispatch.py --catalogue FeaturePlan.json --store STORE \
  --feature family:extrude:cut-extrude submit
```

For P04 evidence, point the following command at a
supervisor registry with the Fusion worker and its capacity-one installation.
Use the same A03 store and source revision as the assessment. The command
waits for the assessment to park, prepares the pinned two-body study, and
commits both native phase jobs and the dependent assessment in one controller
transaction. The existing Fusion owner restart procedure applies between phases.

```shell
python re/automation/InferenceGrid/FeatureDispatch.py --store STORE \
  --feature family:extrude:cut-extrude advance --config SUPERVISOR.json \
  --kind capture.fusion --resource application:fusion:owner --wait-seconds 120
```

Use `status` to inspect the assessment and the attached phase IDs. Repeating
`submit` or `advance` reuses the scheduled work. The original parked receipt is
retained, and only its two affected rescans depend on the successor. Accepted
native observations can still leave the saved target-policy field unresolved.

Each rescan depends on its assessment's accepted controller result. An
unchanged fingerprint reuses the assessment and its counterexamples. Changed
rules and evidence invalidate only declared dependent jobs. Each rescan reads
one pinned native archive, records public reader output identity and retains
the unresolved inventory. A rescan does not apply a research hypothesis to the
production reader.
For paired assessments, the source hash and requested native format must match
the same entry in the accepted report before the reader runs.

### Reuse the SDK across rescans

The offline pilot enables grouped rescans by default. Use `--sessions 1` to
run one Python worker at a time. That worker loads the SDK when its first
archive needs decoding and reuses it while processing the group serially.
Each archive keeps its own input pins, result and receipt. If an archive fails
inside a group, it can retry individually under its usual attempt limit.

For a custom supervisor registry, set `group_protocol` to `1`,
`group_limit_bytes` to `16777216` and `group_peak_memory_mib` to `256` on
`inference.rescan`. Set its `max_memory_mib` to at least `256`. Keep the
pool at `max_sessions: 1` for one physical worker and initialize the controller
with `--max-running 20` to allow up to 20 logical claims in the group.
The controller batches eligible rescans in the same scheduling lane and
family that share their kind, rule and tool revisions. Each group starts
a fresh worker.

## Archive verification

The Workflow quality inference job runs `InferenceArchiveGate.py` through the real
controller and worker supervisor. It checks discovery and affected-file
rescans for the P03 pair. The negative direction control
distinguishes Fusion's signed scalar from SOLIDWORKS' positive magnitude and
separate direction flag. An unchanged resubmission must preserve all receipts.
A rule revision on one side must rerun only that assessment and its attached
archive jobs.

The P04 `inference.paired-gap` job takes a pinned paired report as its plan and
uses no stream input bindings. The termination report records the
blind-to-through-all change and measured volume difference. Its completed
counterexample releases rescans of the four affected archives. The one-body
capture leaves automatic and explicit selection compatible with the same
target. The controller parks this gap until distinguishing evidence arrives
and retains the two-body grid and affected archives in the receipt.

### Provision the scope on the Fusion host

Use a clean checkout at the same full revision as the Fusion installation and a
new owner-private A03 store on that host. Point the supervisor configuration at
this store and register both the inference runner and the
[supervised Fusion worker](../Workers/FusionPhaseQueue.md) in their own pools.
Before the Fusion queue is used, provision the scope and run the supervisor to
get that store's parked receipt.

```shell
uv run --frozen --group dev --python 3.14 python re/automation/Controller.py \
  --store /private/ResearchStore init
uv run --frozen --group dev --python 3.14 python re/automation/InferenceGrid/Provision.py \
  --store /private/ResearchStore --source-revision FULL_CHECKOUT_SHA
uv run --frozen --group dev --python 3.14 python re/automation/Supervisor.py \
  --config /private/Supervisor.json run --idle-seconds 8 --max-seconds 180
uv run --frozen --group dev --python 3.14 python re/automation/Controller.py \
  --store /private/ResearchStore status --job ASSESSMENT_JOB_ID
```

Use the `assessment_job` printed by the provisioner. It pins the original
discovery report and its two affected P04 archives to the assessment and two
rescans. The inference worker issues a new `waiting_evidence` receipt in this
store. Both rescans wait with zero attempts. The provisioner can read back the
same three jobs on an unchanged retry and refuses a different existing scope
definition. The Windows replay receipt remains tied to its original store.

Queue the fixed [Fusion two-body scope study](../FusionReadback/FusionScopeControl.md)
in this same store. Keep the queue receipt from the host's queue command.
Attach it using the newly issued parked assessment receipt and the SHA-256 of
the queue receipt.

```shell
uv run --frozen --group dev --python 3.14 python re/automation/InferenceGrid/Resume.py \
  --store /private/ResearchStore --queue-receipt /private/GridQueue.json \
  --queue-receipt-sha256 QUEUE_SHA256 --parked-receipt-sha256 ASSESSMENT_SHA256
```

The controller retains the previous attempt and schedules a new generation of
the same assessment. Both application phases and all selected output roles
must complete before the successor can run. It verifies the accepted result
and dispatch pins, healthy controls, linked process identities, and saved
archives before admitting the Fusion observations. The assessment remains
parked until independent evidence establishes the saved target-policy meaning.
The original rescan dependencies and frozen holdout stay in place.
With the Fusion resource unavailable, Phase A waits for the application and
Phase B and the assessment wait for evidence.

The hosted integration also exercises a synthetic disjoint-lineage holdout
and a repeated-lineage refusal. P03 and P04 remain discovery evidence. P05
remains reserved. Full milestone acceptance requires qualified A06 paired
evidence and fresh licensed Fusion readback.

The [hosted A07 job](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/job/132964230460)
passed both the archive and scheduler verification at `ebe6130c`. It recorded
16 P03 rescans and four P04 termination rescans. An unchanged replay reused
all 18 P03 assessment and rescan receipts. A rule change reran nine jobs in one
scope. The P04 body-selection request parked with two dependent archives.
The synthetic holdout supported and contradicted the same frozen hypothesis
in separate runs, and the worker refused the repeated lineage.
[Hosted evidence artifact](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/artifacts/14181740600)

The private A07 historical replay at source `8425b5fbc9bbda0b19c9efbd8dc566d2ea6cc0c4` used the original paired P03 and P04 discovery captures from `89c25945f5833ad9c3a1c6c683df510b5702dd54` and the real A03 supervisor. It settled 23 jobs, including 20 rescans, and parked three. An unchanged submission reused all 24 issued receipts with zero new attempts. The P03 negative direction supported the partial signed Fusion candidate while refuting the equivalent signed SOLIDWORKS scalar. The P04 through-all counterexample refuted the shared blind-depth hypothesis and released four rescans. The body-selection assessment and both dependent rescans remained parked. Both rescans had zero attempts.

The retained report SHA-256 is `66a1e22b04c02f004ef662b86d0506959c17efbd85ccca57bafaa1e77e5d1744`. The exact body-selection parked receipt SHA-256 is `06414a895e34601d8866dd0cccff87d82da1cbffd90b4829b0a2cdbd9d293fd2`. Its next evidence is accepted licensed Fusion Phase A/B output from the same A03 store and an independently proven saved target-policy field. P05 stays reserved. The separate hosted inference job passed on the same PR head. [Hosted inference results](https://github.com/TryUniCAD/Kit/actions/runs/43902999977/job/133424485649)

The [standalone Fusion search](../Inference/FusionSignedDepthSearch.md) also
records the second signed-depth copy.

See [the paired history comparison](../Readers/Comparison/ArchivedCutHistory.md)
and [the automation step register](../../../Reference/Research/AutomationSteps.md).
