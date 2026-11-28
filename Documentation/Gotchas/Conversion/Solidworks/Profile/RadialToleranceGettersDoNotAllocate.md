# Radial tolerance getters do not allocate

## Expectation

A radial dimension contains a parameter and supports tolerance queries.
Querying its tolerance could appear to construct a default tolerance automatically.

## Observed behavior

The actual 2026 circle-dimension getter returns its nullable tolerance pointer unchanged.
The ordinary constructor and retained append leave that pointer null.
The parameter is a separately constructed object.
The same offset spelling in the parameter does not identify the dimension's tolerance.

The common tolerance-update helper returns when its actual handle getter returns null.
The recorded fresh precision guard excludes the preceding linked-display mutation branch.
This bounded update creates no replacement tolerance.
A display backup definition can own a different tolerance pointer.

## Workaround

Track dimension, parameter and backup-definition ownership separately.
Preserve nullable object grammar instead of inventing a default tolerance record.
Use the [lifecycle record](../../../../../re/solidworks/records/RadialParameterLifecycle2026.md#null-tolerance-and-retained-parameter-ownership)
for concrete dispatch and precision preconditions.
Later explicit setters and complete saved-state acceptance remain separate work.
