<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Automatic research builder development

`RunRecipeCampaign.py --auto-develop-builders` develops the previously unsupported
SOLIDWORKS `family:planes:offset-plane` from the existing `plane-offset` written
recipe. Automatic development is disabled by default. Other features explicitly
report missing verifier support. Fusion qualification is outside this first scope.

The supported options are XY support, positive direction, one plane, millimetres,
and offsets from 1 to 60 mm on the fixed 40 Ã— 20 Ã— 10 mm block prerequisite.
Qualification establishes this bounded research scope on the exact installed build;
it does not establish exhaustive feature support, complete decoding or conversion.

New Codex builder jobs default to `gpt-6.1-terra`. The selected model is pinned in
the saved job for generation and repair calls. An explicit `--model` overrides
the default; resuming a saved job preserves its original model. See
[Terra builder generation](TerraBuilderGeneration.md).

Codex login jobs reuse a controller-owned provider connection and coalesce
identical generation requests through the shared registry. Global personal
instruction context requires the explicit `--builder-personal-instructions`
authorization. See [builder generation optimizations](BuilderGenerationOptimizations.md)
for ownership, cache identity, accounting and verification boundaries.

## Integration and trust boundaries

PR #207 was inspected while open and unmerged at
`4f9ca0cbb43abd44a0472d3db2f8cf3ab9d72291`. Its existing authoring/decoder workers,
controller queues, artifact store, leases, application resource, ownership helpers,
healthy controls and pause behavior are reused. Published main was reviewed at
`bd16f35d5a8e5c9440c62f8c4809265ec60dd130`; incoming reader work was preserved.
Implementation extends the user's unpublished programme at `ca61c7f7`, in isolated
branch `codex/automatic-builder-development`. The SDK is unchanged. Initial delivery
was local only. On 2026-11-21 the user authorized publishing the source changes to
[PR #207](https://github.com/TryUniCAD/Kit/pull/207), head
`codex/catalogue-native-authoring`, retaining existing history and private evidence.

The job binds the recipe, seed, exact application/API fingerprints, source revision,
explicit options, independent expectations/tolerances, discovery cases and limits.
Missing authorisation, prerequisite, installed metadata, licensed host or observation
capability is a blocker. A separately reserved case commitment precedes generation.

The configured Codex, Claude or local Ollama integration produces a schema-constrained
operation program. It cannot supply acceptance code, tolerances or file instructions.
Trusted parameterized helpers transpile that program into complete C#; those exact
hashed bytes execute inside the owned native worker. Provider tools are disabled.
Prompts contain discovery cases, API metadata, official documentation summaries,
examples and retired structured diagnostics. Active reserves never enter prompts.

The fixed collector observes feature type, operation, support and order, prerequisite
dimensions and relationships, world placement, driving dimensions, units, body count,
volume, centre of mass and bounds. It edits the actual driving distance, checks the
plane's geometric movement, restores it, rebuilds and saves A/E/B documents. Separate
owned processes reopen saved states, with healthy controls before and after each
batch and normal exit required. Missing observations remain unverified. Plane
creation cannot be qualified by unchanged body volume or script exit alone.

Independent verification runs as a separate controller job with frozen expectations.
Only builder defects enter bounded model repair; licence, session, source integrity
and verifier failures block. Every attempt, model reservation, source, output and
failure remains in the owned run directory. Process-released locks protect concurrent
resumes and provider accounting. Unpublished interrupted generation is explicitly
abandoned, retained and charged; resumption starts a fresh bounded attempt.

The candidate is frozen before private qualification cases are dispatched. Failed
qualification invalidates it; exposed cases are durably retired before diagnostics
reach the next generation. Revised code receives fresh reserves. Registration rechecks
accepted native/verifier receipts, their exact dependency ancestry, frozen reserved
roster, candidate source identity and current collector bytes. Immutable runtime
artifacts carry their qualified scope and provenance. A later counterexample writes
a revocation rather than changing the original certificate. Source promotion is
separate and is never performed by this loop.

After registration, independently accepted native sample capture queues the existing
decoder. `BuilderResult.json` separately reports builder qualification, native sample
acceptance, decoder findings and conversion qualification. Conversion remains false.
Native automation and runtime registrations remain research-only.

## Native acceptance procedure

Use a clean committed source checkout, Windows, a licensed installed SOLIDWORKS,
configured provider authentication, the existing catalogue/host JSON, and a snapshot
of installed executable/interop versions, SHA-256, reflected signatures and enums.
Keep all run outputs and runtime registrations outside the source checkout.

```powershell
python -B re/automation/InferenceGrid/RunRecipeCampaign.py `
  --directory C:/Research/BD1 `
  --solidworks-catalogue C:/Research/FeaturePlan.json `
  --solidworks-host C:/Research/SolidWorksHost.json --native-ready `
  --auto-develop-builders --builder-api-metadata C:/Research/ApiMetadata.json `
  --advisor codex --auth login --advice-calls 3 `
  --builder-attempts 3 --builder-model-calls 3 `
  --builder-call-seconds 180 --builder-seconds 1800 `
  --builder-demo-defect --builder-negative-probe
```

`--prepare-only` writes the source-bound job and private reservation without model
or CAD execution. Resume with the same directory and `--auto-develop-builders
--builder-resume`; supply the host and `--native-ready` if it was unavailable during
preparation. `--builder-pause` requests a durable pause. Explicit
`--builder-extra-attempts N --builder-extra-seconds N` extends retained limits on
resume; it does not reset prior usage. Wall time includes pauses. Never edit frozen
source or expectations to make an old job pass: preserve it and start a new job.

The negative probe must reject an actual offset plane on YZ support despite matching
mass. Native creation must succeed and produce independent observations; a creation
exception alone cannot satisfy this gate.
The demo deliberately changes the first real generated program's scale to 2 and
records this human-requested intervention. Native observations must show its wrong
distance, then the model must repair it from structured diagnostics. This proves
repair of an injected real builder defect, not spontaneous model failure. A passing
revision must qualify on three independent reserved cases, register its exact source,
capture a separate sample and finish the dependent decoder with findings retained.

Calls and wall time are hard bounded. The CLI providers cannot enforce a hard USD
or token ceiling: requesting `--builder-max-cost-usd` blocks before transport. Actual
reported token usage is retained; unavailable monetary cost remains null. Local
Ollama supports output-token limits and records zero provider charge. No credential,
vendor DLL, compiled assembly or native document belongs in repository commits.

Completion evidence and current status belong to the
[automation register](../../../../Reference/Research/AutomationSteps.md), step A08k.

## Completed first delivery

The actual local `BD3` run completed with exit 0 at frozen source
`d61c3be47c503471c07cb2de4756505e96f1baf4` on SOLIDWORKS build `34.4.1`
(executable and interop file version `34.4.1.1011`). Its elapsed time was
960.77 seconds, including the retained resource wait and explicit resume.
Later test/documentation commits do not change its native or verifier sources.

| Stage                  | Independently recorded result                                                                                                                                                                            |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Negative control       | A valid YZ plane at X=15 mm was rejected despite matching 8,000 mmÂ³ body volume.                                                                                                                        |
| Attempt 1              | Deliberately injected scale 2 created Z=30/40/70 for requests 15/20/35 mm. Edits reached 25/29/42; restoration correctly returned the actual original 30/40/70, and verification rejected the candidate. |
| Automatic repair       | The second real model call returned scale 1 from structured diagnostics, without a human candidate edit. Discovery passed 15/20/35, edits 25/29/42, restoration and all fresh reopens.                   |
| Reserved qualification | Frozen code passed offsets 29.25/56.75/48.25 mm, edits 29.375/56.875/48.375 mm, restoration and fresh reopen with zero diagnostics. These cases were not disclosed to the generator.                     |
| Separate sample        | S1 requested and measured Z=31 mm, edited to 38, restored to 31, saved A/E/B and reopened each in a third process. Native sample acceptance passed.                                                      |
| Decoder                | Completed deterministically on A/B/E, each with 153 records, 1,406 fields and 55 unresolved findings. Portable completion and conversion qualification remain false.                                     |

The qualified candidate's observations retained one solid body, no surface body,
volume `8000.000000000001` mmÂ³, centre of mass `[20,10,5]` mm and bounds
`[0,0,0,40,20,10]` mm. Target observations matched `RefPlane`, distance type 5,
constraint-base type 11, distance constraint 8, Front Plane support, +Z normal,
MMGS units and the actual driving dimension state 2. The prerequisite's type,
sketch dimensions, support, feature order, operation and relationships were checked.
Fifteen owned application processes closed normally across five batches, with
30 healthy control observations and 33 saved archives reopened in fresh processes.
There was no forced cleanup, and the final host inventory contained no SOLIDWORKS
process. The qualified scope remains only the positive single XY plane, 1â€“60 mm.

Two Codex login calls reported 28,511 input tokens and 64 output tokens, 28,575 total.
Their measured durations were 4.748 and 3.924 seconds. Actual model identity and USD
cost were not reported and remain null. The configured model was the CLI default;
no price or model name is inferred.

The immutable runtime registration is
`891fc21a217133543530aeb9991580f8342aa2191ef8a54efdc52ec4e378ef4c`.
Its candidate digest is
`c63aa53ca033606745f391594216ab088ee423d032ac53bc3cf1fcc933f69c31`;
its exact executed and registered C# SHA-256 is
`a569c80b59d1c2e28ce98018f7d8416b243a303c3f1fceed3a97050b440835b8`.
Qualification native job `builder-native:bc8707b82004adc0c5cde2a8ffa0b6c67a8a33385fc4997b0eff11dd28d6be6e`
is bound to verifier job `builder-verify:82631cf4cabb4d86a7b0fc82e05e75475d2542425b19adb7a121bc1ee3e6458c`.
Decoder result SHA-256 is
`d44c3086d784e1b2f1e60eae16e4c613ea9f8b726f0bdd0687f134259e41ddb6`.
Runtime evidence stays outside the checkout in `.rescratch/BD3`; the registration
and generated C# stay in `.rescratch/BuilderRegistry/<id>`. Source promotion was not
performed. No native archive, ZIP bundle, DLL or compiled assembly is committed.

Per decoded archive, the 55 findings comprise 26 native-only records, 27 retained-byte
semantics gaps, one direction/frame/operation evidence gap and one missing independent
source-inventory/native-acceptance link in the reader evidence. Native builder/sample
acceptance does not close those decoder findings. Full decoding, conversion and Fusion
qualification remain open.

All human interventions are retained: explicit opt-in; the requested fault-injection
demo; BD1's object-only metadata transport fix before any CAD/model call; BD2's
[generated-byte and prerequisite-type corrections](../../../../Gotchas/Research/Workers/Inference/GeneratedBuilderIdentity.md)
before any model call, followed by a fresh source-bound job; and BD3's explicit resume
after a transient shared-oracle lock disappeared. Old evidence was never requalified,
no other process was killed or displaced, and no human repaired a generated candidate.
The private `BuilderDevelopmentInterventions.json` records the external interventions
alongside the loop's own intervention journal.

Eighteen new CLI/controller/worker process checks pass, alongside two unchanged default
campaign checks. They cover opt-in/default behavior, explicit blockers, preparation and
resume provisioning, locks, retained model reservations, negative-gate replay, readiness,
reserved-case retirement, registry rejection, recovery reuse and actual typed worker
transport. Fixture records never establish native qualification. Linux and hosted CI
execution were not performed; the generic tests remain eligible for Linux, and the
Windows platform selection includes their prefix. Black, steering and diff checks pass.
The [exact local staging and commit commands](AutomaticBuilderCommands.md) record
the original local delivery. The later source-only publication to PR #207 does not
change the frozen native acceptance revision or promote runtime artifacts into
repository source. Native documents, ZIP bundles, DLLs and compiled assemblies
remain outside the publication.
