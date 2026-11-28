# November 25 capture-failure record audit

## Behavior

This change adds `re/solidworks/Nov25CaptureFailures.md`, an audit of the 12 capture failures that
the SOLIDWORKS reader/writer plan attributes to a November 25 retry run. The audit searches the
committed repository and full history, records the exact commands used, and lists the committed
run records nearest in time to that run.

## Result

The November 25 retry run has no committed per-case record. The only committed mention is the
plan paragraph on PR #296 (`Documentation/Maintenance/SolidworksReaderWriterPlan.md`, commit
`d9ab9e067`). No committed run records 12 capture failures or a 7 body-measurement / 5
sketch-region split, so there are no artifacts to compare and `re/automation/CompareDecoded.py`
cannot be run against them. The audit reports this as a negative result, lists the nearest
committed run records, and clusters the committed capture-failure records that do exist by root
cause with their real counts: SOLIDWORKS COM/RPC loss and capture shutdown timeouts (re-capture),
the thin-wall side capture (re-capture), and the Fusion snapshot-header guard (decoder-side).

## Usage

Read `re/solidworks/Nov25CaptureFailures.md`. It is evidence only and changes no converter code.

## Limitations

The audit does not classify the 12 failures because their per-case artifacts are not committed.
The nearest committed runs it lists are the SOLIDWORKS feature ladder recovery
(`re/solidworks/FeatureLadderRecovery`, 37 cases, two retained failed attempts) and the Fusion
rim-fillet pack (`re/Fusion/RimFilletPack`, 12 cases, a 7/5 split on Fusion categories).

## Verification

The commands in the audit were run against `main` at `1619f00bf`. `git log --all -S"capture failure"`
returns only the plan commit; `git log --all -S"12 capture"` returns the plan and an unrelated
commit. The audit's inline command block is the complete search record.
