# Topology counts are not collections

## Expectation

Matching topology counts pass the same semantic comparator that checks detailed body geometry.

## Actual behavior

The keys `faces` and `edges` identify both numeric topology counts and geometry collections.
Dispatch based only on these keys sent matching numeric counts to an unordered collection comparison.
That comparison rejected the counts because they were not lists or tuples.
The complete offline control comparison therefore failed even when every measurement agreed.
Missing semantic evidence also reported `failed` instead of `unverified` because the unrelated topology comparison failed.

The [Linux research CLI acceptance run](https://github.com/TryUniCAD/Kit/actions/runs/44909982705/job/136863659770) recorded six affected cases.
Source inspection identified the unconditional collection dispatch in `SemanticEqual`.

## Workaround

Dispatch to unordered comparison only when both values are lists or tuples.
Compare numeric `faces` and `edges` values with the existing numeric rules.
Keep the count and geometry checks separate in each report.
The control, missing-evidence, reordered-geometry, and changed-count process cases cover this boundary.
No local tests ran during this repair.
