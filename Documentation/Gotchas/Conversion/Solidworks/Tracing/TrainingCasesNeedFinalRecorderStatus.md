# Training cases need final recorder status

## Expectation

A successful training case has the same final status in its action result and nested recorder.

## Actual behavior

The radius and diameter training action sets `training_result.passed` after measurements and saved-file checks.
Its inherited recorder initializes its separate top-level `passed` field to false.
The original action flushed that recorder without setting its final status.

Under source `feb8e11db`, both author and fresh reopen/edit actions returned successful case results.
All 46 numeric checks passed, and both batches had healthy controls.
Their four nested recorders retained false top-level statuses with no first failure or cleanup error.
Trace qualification and numeric checks do not erase that reporting discrepancy.

## Workaround

Finalize the nested status from the completed case result, first-failure state, and cleanup errors before flushing.
Preserve the original reports and disclose both statuses when publishing their evidence.
Use a fresh committed batch to verify the corrected recorder behavior.

The [focused correction](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksTrainingCaseStatus.md) changes reporting only.
No old result receives generated-output or held-out acceptance credit.
