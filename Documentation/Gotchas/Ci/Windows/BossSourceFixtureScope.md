# Keep collector source fixtures bounded

## Expectation

A source-admission fixture needs the collector's pinned implementation and its import dependencies.

## Actual behavior

The Boss fixture copied every Python, C# and PowerShell file beneath `re/automation`.
At the failed PR #265 queue candidate this selected 535 files, although the collector pins eighteen files.
Windows staging exceeded the existing twenty-second Git deadline in the launcher-tampering case before source admission ran.

## Workaround

Copy the full collector pin set explicitly, including its thirteen Python imports and five native collector or launcher sources.
Retain the existing readback setup, all five source-admission cases, and the original Git and validation deadlines.
A future collector pin added without a corresponding fixture input must fail clean admission rather than reduce validation.

[Failure evidence](https://github.com/TryUniCAD/Kit/actions/runs/45078729462/job/137382013976)
