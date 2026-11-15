# Tupni input-format recovery workflow

The repository now documents a reusable workflow based on the Tupni paper's
parser-observation method. The [playbook](../../../re/Playbook/Tupni.md) includes
capture coordinates, evidence labels, field/record/constraint recovery,
multi-input generalization and the boundary between research traces and
generative writer rules.

The [first-use ledger](../../../re/solidworks/records/Tupni2026.md) records its
application to the ongoing SOLIDWORKS 2026 investigation. The
[maintained research guide](../../Reference/Research/TupniFormatRecovery.md)
links the procedure and evidence. Native capture and measured improvement are
pending; no existing static finding is retroactively credited to Tupni.

Verification at this revision consists of reading the primary paper, inspecting
the target archive boundary and checking the actual VM architecture and tracing
dependency availability. No local tests were run. Native trace and acceptance
results will be added only after execution.

`re/tooling/tupni/Observe.py` captures an explicitly named process with an
explicit native/emulated realm and caller-selected script. It records package
version, script hash, events, truncation, exceptions and detach outcome. It
limits a capture to at most 60 seconds and fails on script errors, dropped
messages or cleanup failures. `Identity.js` reports the actual process
architecture and selected CAD module bases without changing model state.

On the Windows research host, invoke the Python runner with `--frida-dir`
pointing to a private, pinned Frida installation, `--process SLDWORKS.exe`,
`--realm emulated`, `--script Identity.js`, `--output capture.json` and
`--seconds 5`. This is research instrumentation, never a conversion dependency.
