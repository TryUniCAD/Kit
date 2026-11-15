# Run CLI process coverage before archive compatibility

The existing Fusion compatibility job now runs `tests/convert/Commands` in its own first test step.
The archive step retains every existing codec/API case and follows after CLI process coverage succeeds.
The CLI cases are removed from the archive invocation, so each case still executes once.

This provides earlier process-boundary feedback for conversion and inspection changes.
Earlier combined runs reported their CLI failure summary after more than five minutes of combined execution; see [run 43654362487](https://github.com/TryUniCAD/Kit/actions/runs/43654362487).
The change adds no runner or independent gate and preserves the existing registered compatibility job, timeout, and required checks.
Merge-group execution retains both steps.

Workflow source and formatting were checked.
Accepted-head remote results remain recorded in the CLI PR; no local tests ran.
