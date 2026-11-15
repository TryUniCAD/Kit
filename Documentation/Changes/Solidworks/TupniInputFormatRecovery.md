# Tupni input-format recovery workflow

The repository now documents a reusable workflow based on the Tupni paper's
parser-observation method. The [playbook](../../../re/Playbook/Tupni.md) includes
capture coordinates, evidence labels, field/record/constraint recovery,
multi-input generalization and the boundary between research traces and
generative writer rules.

The [first-use ledger](../../../re/solidworks/records/Tupni2026.md) records its
application to the ongoing SOLIDWORKS 2026 investigation. The
[maintained research guide](../../Reference/Research/TupniFormatRecovery.md)
links the procedure and evidence. The first native loader capture succeeded;
measured improvement remains pending. No existing static finding is
retroactively credited to Tupni.

Verification at this revision consists of reading the primary paper, inspecting
the target archive boundary and checking the actual VM architecture and tracing
dependency availability. No local tests were run. Native trace and acceptance
results will be added only after execution.

`re/tooling/tupni/Observe.py` captures an explicitly named process with an
explicit native/emulated realm and caller-selected script. It records package
version, script hash, events, truncation, exceptions and detach outcome. It
limits the post-action observation window to at most 60 seconds and fails on script errors, dropped
messages or cleanup failures. `Identity.js` reports the actual process
architecture and selected CAD module bases without changing model state.

On the Windows research host, invoke the Python runner with `--frida-dir`
pointing to a private, pinned Frida installation, `--process SLDWORKS.exe`,
`--realm native`, `--script Identity.js`, `--output capture.json` and
`--seconds 5`. This is research instrumentation, never a conversion dependency.

The first successful identity observation used the x64 Python/Frida pair and
Frida's native realm, reporting an x64 CAD process. Selecting the emulated realm
on that client returned an explicit unsupported-OS error. The
[architecture gotcha](../../Gotchas/Conversion/Solidworks/TraceHostAndTargetArchitectures.md)
records the distinction. `Solidworks2026.js` adds version-bound sketch/status,
feature-provenance and archive-primitive observations; `--module-manifest`
requires matching loaded-module disk hashes before hook activation.

`--prepare-script PrepareSolidworks.py` restarts the explicitly authorized,
goal-owned oracle and retains its COM controller until tracing has detached.
`--action-script ExerciseSolidworks.py --action-input training.SLDPRT` opens one
selected training control read-only, rebuilds it, records geometry and feature
errors, and closes it without saving. Initialization, the action and cleanup
are included in total elapsed time, outside the bounded post-action window.
The runner records preparation and action hashes, dialog handling and cleanup
failures. The exercise never obtains a different application from the running
object table. See the [controller lifetime finding](../../Gotchas/Conversion/Solidworks/TraceControllerLifetime.md).

The retained-control run collected 2,693 native boundary events with no dropped
events, script errors or dialogs. Its control rebuilt as one correct solid.
The ledger records the capture digest, observed handlers, fixed argument-type
interpretation and missing original input/base identities. Subsequent captures
retain input hashes and runtime module bases. The native exception observer
records fault addresses, registers and a bounded accurate backtrace, then
forwards the exception unchanged. It does not repair or suppress loader faults.
Clean acceptance runs remain uninstrumented. No instruction-level taint or
generalized writer rule is claimed from this first capture.

The first generated candidate terminated before any feature or sketch read.
Its trace records five earlier system exceptions and a final UI access
violation, with uncertain unwind frames. The observer now adds named C++ and
MFC file/archive throw boundaries when exported, reports candidate MSVC type
metadata without treating it as proved CAD grammar, and records the observed
module images. It preserves setup failures and target termination.
