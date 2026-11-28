# Holdout selection needs independent replay

## Expectation

A candidate that matches the holdout might appear ready for qualification.

## Observed behavior

Discovery inputs can put the same varying value at two offsets. A holdout can
distinguish them, and changing only that holdout can select the other offset
without changing either frozen candidate. See the
[worker process controls](../../../tests/Research/Inference/InferenceBoundaryTests.py).

## Workaround

Use `provisional_holdout_selection` to identify the offset for the next replay.
Use fresh, independent evidence through the existing qualification gate before
promoting a rule. Keep the original holdout and counterexamples with the finding.
