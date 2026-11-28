# Text format discovery includes a registry reminder

## Expectation

A registry with one format previously produced two text lines: the header and one data row.

## Actual behavior

PR #376 adds a final registry-only reminder after all text rows.
The third line is not another adapter or leaked registry state.
The directional CLI integration test still expected two lines and failed before checking the directional columns.
The complete test file reproduces this failure without shard ordering.
See [queue run 46027507049](https://github.com/TryUniCAD/Kit/actions/runs/46027507049/job/140603105400).

## Workaround

Use `kit formats --json` for machine processing.
Text integration checks must require the reminder separately from the header and data rows.
The repaired check requires exactly three lines, the exact reminder, and separate reader and writer extensions and aliases.
