# Controlled radial and circle training observations

The research observer adds an opt-in `radial-training` profile and retained-session [training action](../../../../../re/tooling/tupni/AuthorRadialTraining.py). They record radial flag/handle state, point adjacency, marker transitions and actually reached callback/context/listener boundaries. The existing point and arc array readers are reused. No writer or constructor default is added.

Two specifications are locked before measurement: [the matched radius/diameter pair](../../../../../re/tooling/tupni/RadialTraining.json), SHA-256 `4c9827d10c27766f3dc9dfe05c9de16f757949def4ce7d8b1bd82e2f39e43f01`, and [the separate annulus case](../../../../../re/tooling/tupni/AnnulusTraining.json), SHA-256 `060fc61251afee7c172f731fb7c6501220f6671d0a5a9e69fb3db940028a9383`. They derive only from discovery neutral designs. Held-out native files and existing family locks remain untouched.

## Usage

Use [Observe.py](../../../../../re/tooling/tupni/Observe.py) with `--profile radial-training`, `--realm native`, [RadialTrainingModules.json](../../../../../re/tooling/tupni/RadialTrainingModules.json), the existing retained `PrepareSolidworks.py`, the new action and an explicit job. All eight pinned modules must already be loaded before activation. The selected process must match the prepared controller. Select an unused observation output and a separate unused action-output directory outside the checkout.

The job declares `phase`, `specifications`, `specifications_sha256`, `checkout_root`, `output`, `control`, `control_sha256` and the pinned `oracle_sha256`. Run `author` first between healthy instrumented controls. In a fresh owned process run `reopen-edit` with the prior completed `source_manifest` and required `source_manifest_sha256`; it verifies source identity, edits the declared driving dimension, rebuilds and saves an edited copy. The action directly reuses `AuthorCurves` with the retained controller. It never starts another application, invokes its standalone worker, exits an application or touches licensing.

Per-API checkpoints include ordered phase labels. `Training.json`, per-case records and the observer report retain the exact input/helper/native identities and partial failures. The [observation contract](../../../../../re/solidworks/records/RadialTrainingObservation2026.md) gives the full job, field and trace-admission requirements. [Native hook metadata](../../../../../re/solidworks/records/RadialTrainingHooks2026.json) lists all eleven new sites, complete function spans, instruction hashes and concrete vtable fingerprints.

## Limits and verification

Only static source, Python AST, JavaScript syntax, PE/unwind and bounded native instruction review occurred in the worker. The new action and hooks have not executed. Capture success, remote checks and training results are pending. Mapped hook windows must match their pinned SHA-256 values before activation. Every site records five-/fourteen-byte relocation geometry and bounded incoming-target checks. The six interior sites use instruction-probe functions. Before owned closes and controls, capture is paused and tracked display pointers are cleared. Missing reads, unsupported concrete classes and bounded-count failures remain explicit incomplete states. The runner marks incomplete/missing/error traces unqualified and returns nonzero, retaining per-case counts and reasons. The unique-search hook intentionally leaves unsupported SIMD radius/step capture null; it does not substitute general-purpose register values.

The training action's success means its controlled workflow completed. Field closure, callback effects and native acceptance remain false. Compare actual identities and complete lifecycle events separately from process exit and equal words. External listener implementations are not bound or invoked by the observer. Instrumented training never substitutes for clean generated-output measurements.

The annulus discovery coordinate mismatch separates a particular constructor path from completed saved state. The [registrar correction](../../../../../re/solidworks/records/CircleAdjacencyRegistration2026.md) independently explains single `h1` with two role uses; cleanup is not assumed necessary. Point serialization itself can clear adjacency pointers before store; see the [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Model/PointAdjacencyCanChangeDuringSerialization.md). Neither that static rule nor a captured row proves a universal marker angle, null handle, callback no-op or complete radial flag word. No donor values, runtime production dependency, schema change or writer default is introduced. The [CAD criteria](../../../../Reference/Operations/CadSuccessCriteria.md) remain authoritative:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.

The [instruction-probe API gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/InstructionProbesNeedProbeCallbacks.md) and [relocation-safety gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/InstructionBoundariesDoNotProveHookSafety.md) distinguish valid instructions, mapped identity and safe interception. No runtime relocation success is claimed.

The [PowerShell transport gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/ParallelsPowerShellNeedsEncodedCommands.md) records a separate read-only preflight quoting failure and its encoded-command workaround.
That inventory changed no CAD or licensing process.

## First activation result

The [first attempt receipt](../../../../../re/solidworks/measurements/2026/RadialTrainingAuthor01.json) binds committed source `3a8f7180627c1402bd5059a839f27e57eaf7c0a2`.
All eight required original module identities and eleven mapped instruction prefixes matched.
Checked Frida interception rejected UI site `0x492b031a` before the action or controls started.
No native events or model measurements were collected.
The trace is unqualified and earns no native acceptance credit.
Detach, owned cleanup and host exit completed without a reported crash.
The subsequent inventory found no SOLIDWORKS process and preserved the license-server PIDs.
Review another observation boundary before a fresh controlled run.
