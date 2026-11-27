# A nested research process can encounter a staging rename denial

## Expectation

A task-owned research child can publish its completed private stage into an unused output directory.

## Observed behavior

One managed Windows run returned `WinError 5` while renaming its private encoder stage.
The failure occurred before the final capture directory appeared.
The same offline comparison, run with scoped approved execution and another unused destination, completed successfully.
Its research child returned incomplete exit `3`, with no encoder output.
This observation does not identify the operating system's reason for denying the first rename.

## Workaround

Preserve the first failure and check whether its final destination exists.
Use a new task-owned output directory for an authorized retry.
Do not treat a private stage or a rename failure as a completed decode or conversion.

See the [comparison method and evidence](../../../../../re/solidworks/NativeBossProof/Findings.md).
