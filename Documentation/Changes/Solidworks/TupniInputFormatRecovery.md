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
[architecture gotcha](../../Gotchas/Conversion/Solidworks/Tracing/TraceHostAndTargetArchitectures.md)
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
object table. See the [controller lifetime finding](../../Gotchas/Conversion/Solidworks/Tracing/TraceControllerLifetime.md).

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

Tracing gotchas now live in a focused `Tracing/` subdirectory. Remote path
policy identified 33 direct files in the SOLIDWORKS gotchas directory, above
the unchanged limit of 32. Four tracing entries moved together and their links
were updated; the directory limit and CI gate remain enabled.

The first generated-file fault was narrowed through actual C++ exception
observation and an instruction-site probe at the archive schema comparison.
The probe identified `uoJournal_c` requiring schema zero. Static registered-class
metadata corroborated this and found the same requirement for
`su_CStringArray`; both fresh constructors were corrected. The
[actual-use ledger](../../../re/solidworks/records/Tupni2026.md#first-recovered-rule-registered-class-schemas)
records capture and binary hashes, exact addresses, the rejected input and
evidence limits. This is an observed, binary-backed format correction, not full
instruction taint or a measured speedup. Clean acceptance of corrected generated
files remains pending.

The observer now passes its retained trace interface to an explicitly selected
action. `AuthorPolygons.py` brackets native document creation, sketch/feature
authoring, first explicit rebuild, save and close with phase events. It accepts
one JSON job naming `specifications`, `output` and a known `control`; its source
specifications contain at most three training models. It records actual native
point/segment/relation counts and geometry, helper/input hashes, and controls
before and after in the same instrumented process. These are training
observations, not clean generated-file acceptance.

Additional version-bound probes cover complete sketch updates, coordinate
commit counts, mapped solver statuses and independent header update/body stamp
allocation. The module manifest now also requires the exact archive module
hash. A mapped status event is explicitly observed before its caller resumes;
it does not claim the subsequent entity setter has executed. Runtime sketch
cache pointers remain distinct from similarly numbered profile fields. The
new capture results will be recorded after execution; no status or stamp value
is inferred from instrumentation setup alone.

The corrected candidate's second capture confirms the journal schema comparison
now matches zero and the loader reaches the part root. It then throws archive
cause five. Native `ReadObject` explains this as an object index beyond the
current read-map length, distinct from the earlier schema mismatch. Probes now
record object dispatch, the returned class-reader tag, requested runtime class,
current buffer cursor and map length. These identify a concrete reference
failure without treating an uncertain system unwind as a call chain. Absolute
logical stream offsets remain unknown until an independently verified mapping
exists.

`--profile loader` limits observations to class/object dispatch, exceptions and
part serialization's archive-context version selection. `--profile sketch`
captures sketch lifecycle and stamp boundaries without the full object-dispatch
traffic; `full` retains both. The manifest also verifies `sldmfcu.dll` before
its helper and version probes activate. Class-reader schema outputs are omitted
when that native branch does not initialize them, and runtime class names stop
at their terminator.

The first polygon-authoring attempt failed its preceding control and authored
no training case. That action selected the privacy-redacted parser fixture
instead of the original vendor-saved control used in earlier healthy oracle
runs. This capture is discarded for inference; the cause of its process death
is not attributed to redaction without further evidence. Subsequent oracle
jobs explicitly identify the original control by its separate SHA-256.

Response files use the standard `@path` argument form, with one complete
argument per line. The runner records their digests and the actual working
directory. This keeps Parallels commands short without changing the oracle's
working directory. The authoring action now inspects controls read-only through
the previously successful retained-controller path and records the control
digest. A second authoring setup also failed before creating a case; no solver
rule is inferred from either failed control.

The original control also failed with the previous exception instrumentation.
Exception-function hooks and the process exception handler now require explicit
`--exception-probes`; ordinary parser/status profiles install neither. This
isolates the instrumentation during healthy-control checks. It does not suppress
document errors: open/rebuild results, target termination, script failures and
dialog records remain visible. The precise cause of the traced-control failure
remains unproven until the reduced observation is compared with a healthy run.
