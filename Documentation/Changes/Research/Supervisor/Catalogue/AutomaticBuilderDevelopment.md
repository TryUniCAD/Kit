<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

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
and offsets from 1 to 60 mm on the fixed 40 × 20 × 10 mm block prerequisite.
Qualification establishes this bounded research scope on the exact installed build;
it does not establish exhaustive feature support, complete decoding or conversion.

## Integration and trust boundaries

PR #207 was inspected while open and unmerged at
`4f9ca0cbb43abd44a0472d3db2f8cf3ab9d72291`. Its existing authoring/decoder workers,
controller queues, artifact store, leases, application resource, ownership helpers,
healthy controls and pause behavior are reused. Published main was reviewed at
`bd16f35d5a8e5c9440c62f8c4809265ec60dd130`; incoming reader work was preserved.
Implementation extends the user's unpublished programme at `ca61c7f7`, in isolated
branch `codex/automatic-builder-development`. The SDK is unchanged. Nothing is pushed.

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
Native qualification remains unverified until its actual acceptance run is recorded.
