# Consistent training case status

The radial training action now finalizes each nested recorder's `passed` field before flushing its result.
Success requires a completed case result, no first failure, and no cleanup errors.
An exception still exits through the existing failure path.

The earlier author and reopen/edit actions reported successful cases, healthy controls, and 46 passing numeric checks.
Their nested recorders retained the initial false status because the action did not finalize that separate field.
The [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/TrainingCasesNeedFinalRecorderStatus.md) explains the discrepancy.
Original reports remain immutable and retain their original statuses.

Source and AST inspection verify the correction without executing the action or a local test.
Fresh controlled verification of the corrected nested status remains pending.
This change establishes no writer, field closure, or native generated-output acceptance.
